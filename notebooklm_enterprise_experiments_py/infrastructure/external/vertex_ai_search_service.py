"""Vertex AI Search (Discovery Engine) サービス実装。"""

from pathlib import Path
from typing import Any

from google.cloud import discoveryengine_v1 as discoveryengine
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

    SearchServiceClientを使用してWebサイトデータに対する検索と
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

        # SearchServiceClientの初期化
        self.search_client = discoveryengine.SearchServiceClient(
            credentials=credentials
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

        # ContentSearchSpecの設定（要約を有効化）
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
                language_code="ja",
            ),
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_answer_count=3,
            ),
        )

        # SearchRequestの作成
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=10,
            content_search_spec=content_search_spec,
        )

        # 検索を実行
        response = self.search_client.search(request=request)

        # レスポンスから結果をパース
        return self._parse_response(response)

    def _parse_response(
        self, response: Any
    ) -> SearchResult:
        """SearchResponseをパースしてSearchResultを返す。

        Args:
            response: Discovery Engineからの検索レスポンス（SearchPager）

        Returns:
            SearchResult: パースされた検索結果
        """
        # サマリーの取得
        summary_text = ""
        if response.summary and response.summary.summary_text:
            summary_text = response.summary.summary_text

        # 引用情報の取得
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
