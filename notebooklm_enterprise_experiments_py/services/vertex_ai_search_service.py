"""Vertex AI Search (Discovery Engine) サービス実装。"""

from pathlib import Path
from typing import Any

from google.api_core import exceptions as google_exceptions
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.oauth2 import service_account

from notebooklm_enterprise_experiments_py.config.env_config import (
    get_service_account_key_info,
    get_service_account_key_path,
)
from notebooklm_enterprise_experiments_py.models.search import (
    DocumentResult,
    DocumentSearchResult,
    ISearchService,
    SearchCitation,
    SearchResult,
)


class VertexAISearchService(ISearchService):
    """Vertex AI Search (Discovery Engine) を使用した検索サービス。

    SearchServiceClientを使用してWebサイトデータに対する検索と
    AIによる回答要約生成を行う。
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        engine_id: str,
        credentials: service_account.Credentials | None = None,
    ) -> None:
        """VertexAISearchServiceを初期化する。

        Args:
            project_id: GCPプロジェクトID
            location: GCPロケーション（例: "global"）
            engine_id: 検索アプリ（Engine）のID
            credentials: サービスアカウント認証情報（Noneの場合は環境変数から取得）
        """
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id

        if credentials is None:
            credentials = self._load_credentials()

        # SearchServiceClientの初期化
        # locationに応じてエンドポイントを設定
        client_options = None
        if location != "global":
            client_options = ClientOptions(
                api_endpoint=f"{location}-discoveryengine.googleapis.com"
            )

        self.search_client = discoveryengine.SearchServiceClient(
            credentials=credentials,
            client_options=client_options,
        )

        # serving_configのパスを構築
        # Generic Search Appでは /engines/ を使用する必要がある
        # (serving_config_pathヘルパーは /dataStores/ を生成するため使用しない)
        self.serving_config = (
            f"projects/{self.project_id}/locations/{self.location}"
            f"/collections/default_collection/engines/{self.engine_id}"
            f"/servingConfigs/default_serving_config"
        )

    def _load_credentials(self) -> service_account.Credentials:
        """環境変数からサービスアカウント認証情報を読み込む。

        Returns:
            サービスアカウント認証情報

        Raises:
            ValueError: 認証情報が設定されていない場合
        """
        # まず、JSON文字列から読み込むことを試みる
        key_info = get_service_account_key_info()
        if key_info:
            return service_account.Credentials.from_service_account_info(key_info)

        # 次に、ファイルパスから読み込むことを試みる
        key_path = get_service_account_key_path()
        if key_path:
            key_path_obj = Path(key_path)
            if not key_path_obj.exists():
                raise ValueError(
                    f"サービスアカウントキーファイルが見つかりません: {key_path}"
                )
            return service_account.Credentials.from_service_account_file(
                str(key_path_obj)
            )

        raise ValueError(
            "サービスアカウント認証情報が設定されていません。"
            "GCP_SERVICE_ACCOUNT_KEY_PATHまたはGCP_SERVICE_ACCOUNT_KEY_JSONを設定してください。"
        )

    def search_and_answer(self, query: str) -> SearchResult:
        """検索と同時にAIによる要約（回答）を取得する。

        Args:
            query: 検索クエリ（質問テキスト）

        Returns:
            SearchResult: summary（回答テキスト）とcitations（引用元リスト）を含む結果
        """
        # ContentSearchSpecの設定（要約を有効化）
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,  # 上位5件を回答生成に使用
                include_citations=True,  # 引用元を含める
                ignore_non_summary_seeking_query=True,  # 質問形式でなくても回答を強制
                ignore_adversarial_query=True,  # フィルタを緩和
                language_code="ja",  # 日本語指定
            ),
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
            ),
        )

        # SearchRequestの作成
        request = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=5,
            content_search_spec=content_search_spec,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
            ),
        )

        # 検索を実行
        response = self.search_client.search(request=request)

        # デバッグ出力
        print(f"[DEBUG] Response type: {type(response)}")
        if response.summary:
            summary_text = response.summary.summary_text
            if summary_text:
                print(f"[DEBUG] Summary: '{summary_text[:200]}...'")
            else:
                print("[DEBUG] Summary: (empty)")
            if response.summary.summary_skipped_reasons:
                reasons = response.summary.summary_skipped_reasons
                print(f"[DEBUG] Skipped Reasons: {reasons}")
        else:
            print("[DEBUG] Summary: None")

        # レスポンスから結果をパース
        return self._parse_response(response)

    def search_documents(
        self,
        query: str,
        page_size: int = 20,
        filter_str: str | None = None,
        order_by: str | None = None,
    ) -> DocumentSearchResult:
        """ドキュメント検索を実行し、検索結果リストを返す。

        API側での要約（summary_spec）を使用せず、検索結果（スニペット/抽出コンテンツ）
        を大量に取得する。取得した結果はGeminiモデルに渡して回答生成に使用する。

        Args:
            query: 検索クエリ（質問テキスト）
            page_size: 取得する検索結果の件数（デフォルト: 20）
            filter_str: フィルタ条件（例: "date >= '2026-01-26'"）
            order_by: ソート順（例: "date desc"）

        Returns:
            DocumentSearchResult: 検索結果のドキュメントリスト
        """
        # ContentSearchSpecの設定（要約なし、スニペット/抽出コンテンツを取得）
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=3,  # 最大3スニペット（フォールバック用）
            ),
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_answer_count=2,  # 各ドキュメントから最大2つの抽出回答
                max_extractive_segment_count=3,  # 各結果から最大3つの抽出セグメント
                num_previous_segments=1,  # 文脈を広げるため前後のセグメントも取得
                num_next_segments=1,
                return_extractive_segment_score=True,  # 関連度スコアを取得
            ),
        )

        # SearchRequestの作成
        request_params = {
            "serving_config": self.serving_config,
            "query": query,
            "page_size": page_size,
            "content_search_spec": content_search_spec,
            "query_expansion_spec": discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            "spell_correction_spec": discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
            ),
        }

        # フィルタ条件があれば追加
        if filter_str:
            request_params["filter"] = filter_str
            print(f"[DEBUG] Filter: {filter_str}")

        # ソート順があれば追加
        if order_by:
            request_params["order_by"] = order_by
            print(f"[DEBUG] Order by: {order_by}")

        request = discoveryengine.SearchRequest(**request_params)

        # 検索を実行（フィルタエラー時はフォールバック）
        try:
            response = self.search_client.search(request=request)

            # デバッグ出力
            result_count = sum(1 for _ in response.results)
            print(f"[DEBUG] Search returned {result_count} results")

            # 再度イテレーション（response.resultsはイテレータなので再取得が必要）
            response = self.search_client.search(request=request)

        except google_exceptions.InvalidArgument as e:
            error_msg = str(e)
            # フィルタ/ソートに関するエラーの場合はフォールバック
            filter_errors = [
                "Unsupported field",
                "Invalid filter syntax",
                "Unsupported rhs value",
                "Parsing filter failed",
            ]
            if any(err in error_msg for err in filter_errors):
                print(
                    "[WARNING] フィルタ/ソート構文エラー。フィルタなしで再検索します。"
                )
                print(f"[DEBUG] エラー詳細: {error_msg[:200]}")
                # フィルタ/ソートなしで再検索
                request_params.pop("filter", None)
                request_params.pop("order_by", None)
                request = discoveryengine.SearchRequest(**request_params)
                response = self.search_client.search(request=request)
            else:
                raise

        # レスポンスをパースしてDocumentSearchResultを返す
        return self._parse_document_response(response)

    def _parse_document_response(self, response: Any) -> DocumentSearchResult:
        """SearchResponseをパースしてDocumentSearchResultを返す。

        Args:
            response: Discovery Engineからの検索レスポンス

        Returns:
            DocumentSearchResult: パースされた検索結果
        """
        documents: list[DocumentResult] = []

        for result in response.results:
            document = result.document
            if not document:
                continue

            # derived_struct_dataからメタデータを取得
            data = document.derived_struct_data
            if not data:
                continue

            # デバッグログ: レスポンス構造を確認
            print(f"\n[DEBUG] Result Keys: {list(data.keys())}")

            title = str(data.get("title", "無題"))
            url = str(data.get("link", ""))

            # --- ロバストなテキスト抽出ロジック ---
            # 抽出対象のリスト候補をすべて収集
            sources: list[Any] = []
            if "extractive_segments" in data:
                sources.extend(data["extractive_segments"])
            if "extractive_answers" in data:
                sources.extend(data["extractive_answers"])
            if "snippets" in data:
                sources.extend(data["snippets"])

            content_parts: list[str] = []

            for source_obj in sources:
                # 1. まずは一般的なキー名をチェック
                found_text = None
                if hasattr(source_obj, "get"):
                    found_text = (
                        source_obj.get("content")
                        or source_obj.get("snippet")
                        or source_obj.get("htmlSnippet")
                        or source_obj.get("text")
                    )

                # 2. 見つからなければ、値の中から「最も長い文字列」を探す
                if not found_text:
                    longest_str = ""
                    try:
                        for val in dict(source_obj).values():
                            if isinstance(val, str) and len(val) > len(longest_str):
                                longest_str = val
                        if len(longest_str) > 10:  # 短いノイズは除外
                            found_text = longest_str
                    except (TypeError, ValueError):
                        pass

                if found_text:
                    # HTMLタグ除去（簡易的）
                    clean_text = (
                        found_text.replace("<b>", "")
                        .replace("</b>", "")
                        .replace("\n", " ")
                    )
                    content_parts.append(clean_text)

            # コンテンツを結合
            full_content = "\n\n".join(content_parts)

            # デバッグログ
            content_len = len(full_content)
            print(f"[DEBUG] {title} | Sources:{len(sources)} | Len:{content_len}")
            if sources and not full_content:
                print(f"[DEBUG] Failed: {dict(sources[0])}")

            # コンテンツが空の場合はフォールバック
            if not full_content:
                full_content = "(本文なし)"

            documents.append(
                DocumentResult(
                    title=title,
                    content=full_content,
                    url=url,
                )
            )

        return DocumentSearchResult(results=documents)

    def _parse_response(self, response: Any) -> SearchResult:
        """SearchResponseをパースしてSearchResultを返す。

        Args:
            response: Discovery Engineからの検索レスポンス

        Returns:
            SearchResult: パースされた検索結果
        """
        # サマリーの取得
        summary_text = ""
        if response.summary and response.summary.summary_text:
            summary_text = response.summary.summary_text

        # 引用情報の取得（検索結果から）
        citations: list[SearchCitation] = []
        for result in response.results:
            document = result.document
            if document and document.derived_struct_data:
                # derived_struct_dataからタイトルとURLを取得
                struct_data = dict(document.derived_struct_data)
                title = struct_data.get("title", "")
                url = struct_data.get("link", "")

                if title or url:
                    citations.append(
                        SearchCitation(
                            title=str(title) if title else "無題",
                            url=str(url) if url else "",
                        )
                    )

        return SearchResult(summary=summary_text, citations=citations)
