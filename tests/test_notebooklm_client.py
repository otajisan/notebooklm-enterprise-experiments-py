"""NotebookLMClientのテスト。"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.oauth2 import service_account

# モジュール全体をモックする前にインポート
with patch(
    "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine"
) as mock_discoveryengine:
    mock_discoveryengine.NotebookServiceClient = Mock
    mock_discoveryengine.ConversationalSearchServiceClient = Mock
    mock_discoveryengine.Notebook = Mock
    mock_discoveryengine.CreateNotebookRequest = Mock
    mock_discoveryengine.ImportNotebookSourcesRequest = Mock
    mock_discoveryengine.GcsSource = Mock
    mock_discoveryengine.AnswerRequest = Mock
    mock_discoveryengine.Query = Mock
    mock_discoveryengine.AnswerRequest.AnswerGenerationSpec = Mock

from notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client import (  # noqa: E501
    NotebookLMClient,
)


class TestNotebookLMClient:
    """NotebookLMClientのテスト。"""

    @pytest.fixture
    def mock_credentials(self) -> service_account.Credentials:
        """モック認証情報を作成する。"""
        return Mock(spec=service_account.Credentials)

    @pytest.fixture
    def client(self, mock_credentials: service_account.Credentials) -> NotebookLMClient:
        """NotebookLMClientのインスタンスを作成する。"""
        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=Mock(),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
                credentials=mock_credentials,
            )
            return client

    def test_init_with_credentials(
        self, mock_credentials: service_account.Credentials
    ) -> None:
        """認証情報を指定して初期化できる。"""
        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=Mock(),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
                credentials=mock_credentials,
            )
            assert client.project_id == "test-project"
            assert client.location == "global"

    def test_init_without_credentials_uses_env(self) -> None:
        """認証情報が指定されていない場合は環境変数から読み込む。"""
        key_info = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
        }
        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.get_service_account_key_info",
                return_value=key_info,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.service_account.Credentials.from_service_account_info",
                return_value=Mock(spec=service_account.Credentials),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=Mock(),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
            )
            assert client.project_id == "test-project"
            assert client.location == "global"

    def test_init_without_credentials_uses_file_path(self, tmp_path: Path) -> None:
        """認証情報が指定されていない場合はファイルパスから読み込む。"""
        key_file = tmp_path / "key.json"
        key_file.write_text('{"type": "service_account"}')

        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.get_service_account_key_info",
                return_value=None,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.get_service_account_key_path",
                return_value=str(key_file),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.service_account.Credentials.from_service_account_file",
                return_value=Mock(spec=service_account.Credentials),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=Mock(),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
            )
            assert client.project_id == "test-project"
            assert client.location == "global"

    def test_init_without_credentials_raises_error(self) -> None:
        """認証情報が設定されていない場合はエラーを発生させる。"""
        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.get_service_account_key_info",
                return_value=None,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.get_service_account_key_path",
                return_value=None,
            ),
        ):
            with pytest.raises(
                ValueError,
                match="サービスアカウント認証情報が設定されていません",
            ):
                NotebookLMClient(
                    project_id="test-project",
                    location="global",
                )

    def test_create_notebook(
        self, mock_credentials: service_account.Credentials
    ) -> None:
        """ノートブックを作成できる。"""
        mock_notebook_client = Mock()
        mock_response = Mock()
        mock_notebook_client.create_notebook = MagicMock(return_value=mock_response)

        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=mock_notebook_client,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
                credentials=mock_credentials,
            )

            result = client.create_notebook(
                notebook_id="test-notebook",
                display_name="テストノートブック",
            )

            assert result == mock_response
            mock_notebook_client.create_notebook.assert_called_once()
            call_args = mock_notebook_client.create_notebook.call_args
            assert call_args[1]["request"].notebook_id == "test-notebook"
            assert call_args[1]["request"].notebook.display_name == "テストノートブック"

    def test_add_sources(self, mock_credentials: service_account.Credentials) -> None:
        """ソースを追加できる。"""
        mock_notebook_client = Mock()
        mock_operation = Mock()
        mock_operation.result = MagicMock(return_value=None)
        mock_notebook_client.import_notebook_sources = MagicMock(
            return_value=mock_operation
        )

        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=mock_notebook_client,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=Mock(),
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
                credentials=mock_credentials,
            )

            client.add_sources(
                notebook_id="test-notebook",
                source_uris=["gs://bucket/doc1.pdf", "gs://bucket/doc2.pdf"],
            )

            mock_notebook_client.import_notebook_sources.assert_called_once()
            call_args = mock_notebook_client.import_notebook_sources.call_args
            assert len(call_args[1]["request"].gcs_source.uris) == 2
            assert "gs://bucket/doc1.pdf" in call_args[1]["request"].gcs_source.uris
            assert "gs://bucket/doc2.pdf" in call_args[1]["request"].gcs_source.uris

    def test_ask(self, mock_credentials: service_account.Credentials) -> None:
        """質問できる。"""
        mock_conversational_client = Mock()
        mock_answer = Mock()
        mock_answer.answer_text = "これは回答です。"
        mock_answer.citations = []
        mock_response = Mock()
        mock_response.answer = mock_answer
        mock_conversational_client.answer = MagicMock(return_value=mock_response)

        with (
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.NotebookServiceClient",
                return_value=Mock(),
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client.discoveryengine.ConversationalSearchServiceClient",
                return_value=mock_conversational_client,
            ),
        ):
            client = NotebookLMClient(
                project_id="test-project",
                location="global",
                credentials=mock_credentials,
            )

            result = client.ask(
                notebook_id="test-notebook",
                query_text="最新の売上状況は？",
            )

            assert result == mock_response
            mock_conversational_client.answer.assert_called_once()
            call_args = mock_conversational_client.answer.call_args
            assert call_args[1]["request"].query.text == "最新の売上状況は？"
