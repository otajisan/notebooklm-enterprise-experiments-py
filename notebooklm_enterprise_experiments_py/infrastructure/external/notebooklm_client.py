"""NotebookLMクライアント（Google Cloud Discovery Engine）。"""

from pathlib import Path
from typing import Any

from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.oauth2 import service_account

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (
    get_service_account_key_info,
    get_service_account_key_path,
)


class NotebookLMClient:
    """NotebookLM（Google Cloud Discovery Engine）との通信を行うクライアント。"""

    def __init__(
        self,
        project_id: str,
        location: str,
        credentials: service_account.Credentials | None = None,
    ) -> None:
        """NotebookLMClientを初期化する。

        Args:
            project_id: GCPプロジェクトID
            location: GCPロケーション（例: "global"）
            credentials: サービスアカウント認証情報（Noneの場合は環境変数から取得）
        """
        self.project_id = project_id
        self.location = location

        if credentials is None:
            credentials = self._load_credentials()

        self.notebook_client = discoveryengine.NotebookServiceClient(  # type: ignore[attr-defined]
            credentials=credentials
        )
        self.conversational_search_client = (
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

    def create_notebook(
        self,
        notebook_id: str,
        display_name: str,
    ) -> Any:
        """ノートブックを作成する。

        Args:
            notebook_id: ノートブックID
            display_name: 表示名

        Returns:
            作成されたノートブック
        """
        parent = f"projects/{self.project_id}/locations/{self.location}"

        notebook = discoveryengine.Notebook(display_name=display_name)  # type: ignore[attr-defined]

        request = discoveryengine.CreateNotebookRequest(  # type: ignore[attr-defined]
            parent=parent,
            notebook=notebook,
            notebook_id=notebook_id,
        )

        response = self.notebook_client.create_notebook(request=request)
        return response

    def add_sources(
        self,
        notebook_id: str,
        source_uris: list[str],
    ) -> None:
        """ノートブックにソースを追加する。

        Args:
            notebook_id: ノートブックID
            source_uris: 追加するソースURIのリスト（GCS URI）
        """
        name = (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"notebooks/{notebook_id}"
        )

        request = discoveryengine.ImportNotebookSourcesRequest(  # type: ignore[attr-defined]
            parent=name,
            gcs_source=discoveryengine.GcsSource(uris=source_uris),  # type: ignore[attr-defined]
        )

        operation = self.notebook_client.import_notebook_sources(request=request)
        operation.result()  # 操作が完了するまで待機

    def ask(
        self,
        notebook_id: str,
        query_text: str,
        include_citations: bool = True,
    ) -> Any:
        """ノートブックに質問する。

        Args:
            notebook_id: ノートブックID
            query_text: 質問テキスト
            include_citations: 引用を含めるかどうか

        Returns:
            回答レスポンス
        """
        serving_config = (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"collections/default_collection/engines/{notebook_id}/"
            f"servingConfigs/default_serving_config"
        )

        request = discoveryengine.AnswerRequest(  # type: ignore[attr-defined]
            serving_config=serving_config,
            query=discoveryengine.Query(text=query_text),  # type: ignore[attr-defined]
            answer_generation_spec=discoveryengine.AnswerRequest.AnswerGenerationSpec(  # type: ignore[attr-defined]
                include_citations=include_citations
            )
            if include_citations
            else None,
        )

        response = self.conversational_search_client.answer(request=request)  # type: ignore[attr-defined]
        return response
