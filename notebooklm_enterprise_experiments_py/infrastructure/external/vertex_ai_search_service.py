"""Vertex AI Search (Discovery Engine) サービス実装。"""

from pathlib import Path
from typing import Any

from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.oauth2 import service_account

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (
    get_service_account_key_info,
    get_service_account_key_path,
)
from notebooklm_enterprise_experiments_py.interfaces.search_interface import (
    ISearchService,
    SearchCitation,
    SearchResult,
)


class VertexAISearchService(ISearchService):
    """Vertex AI Search (Discovery Engine) を使用した検索サービス。

    ConversationalSearchServiceClientを使用してWebサイトデータに対する
    AIによる回答生成を行う。
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

        # ConversationalSearchServiceClientの初期化（AI回答生成用）
        self.conversational_client = (
            discoveryengine.ConversationalSearchServiceClient(credentials=credentials)
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

    def _build_serving_config_path(self) -> str:
        """serving_configのパスを構築する。

        Returns:
            serving_configのフルパス
        """
        return (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"collections/default_collection/engines/{self.engine_id}/"
            f"servingConfigs/default_serving_config"
        )

    def search_and_answer(self, query: str) -> SearchResult:
        """検索と同時にAIによる要約（回答）を取得する。

        Args:
            query: 検索クエリ（質問テキスト）

        Returns:
            SearchResult: summary（回答テキスト）とcitations（引用元リスト）を含む結果
        """
        serving_config = self._build_serving_config_path()

        # AnswerQueryRequestの作成（AI回答生成用）
        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config,
            query=discoveryengine.Query(text=query),
            answer_generation_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
                include_citations=True,
                # 各種フィルタを無効化して回答生成を試みる
                ignore_adversarial_query=True,
                ignore_non_answer_seeking_query=True,
                ignore_low_relevant_content=True,
            ),
        )

        # 回答を取得
        response = self.conversational_client.answer_query(request=request)

        # デバッグ出力
        print(f"[DEBUG] Response type: {type(response)}")
        if response.answer:
            print(f"[DEBUG] Answer text: '{response.answer.answer_text[:200]}...'")
            print(f"[DEBUG] Answer state: {response.answer.state}")
            skipped = response.answer.answer_skipped_reasons
            print(f"[DEBUG] Answer skipped reasons: {skipped}")
            print(f"[DEBUG] References count: {len(response.answer.references)}")
            print(f"[DEBUG] Citations count: {len(response.answer.citations)}")
            # 参照情報を出力
            for i, ref in enumerate(response.answer.references[:3]):
                print(f"[DEBUG] Reference {i}: {ref}")
        else:
            print("[DEBUG] Answer: None")

        # レスポンスから結果をパース
        return self._parse_response(response)

    def _parse_response(self, response: Any) -> SearchResult:
        """AnswerResponseをパースしてSearchResultを返す。

        Args:
            response: Discovery EngineからのAnswerレスポンス

        Returns:
            SearchResult: パースされた検索結果
        """
        # 回答テキストの取得
        summary_text = ""
        if response.answer and response.answer.answer_text:
            summary_text = response.answer.answer_text

        # 引用情報の取得
        citations: list[SearchCitation] = []
        if response.answer and response.answer.citations:
            for citation in response.answer.citations:
                for source in citation.sources:
                    # reference_indexから対応するreferenceを取得
                    ref_index = source.reference_index
                    if ref_index < len(response.answer.references):
                        ref = response.answer.references[ref_index]
                        # unstructured_document_infoからURLとタイトルを取得
                        if ref.unstructured_document_info:
                            doc_info = ref.unstructured_document_info
                            uri = doc_info.uri if doc_info.uri else ""
                            title = doc_info.title if doc_info.title else "無題"
                            # 重複チェック
                            if not any(c.url == uri for c in citations):
                                citations.append(
                                    SearchCitation(title=str(title), url=str(uri))
                                )

        return SearchResult(summary=summary_text, citations=citations)
