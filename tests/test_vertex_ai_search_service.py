"""VertexAISearchServiceのテスト。"""

from unittest.mock import MagicMock, patch

import pytest

from notebooklm_enterprise_experiments_py.infrastructure.external import (
    vertex_ai_search_service,
)
from notebooklm_enterprise_experiments_py.interfaces.search_interface import (
    SearchResult,
)

VertexAISearchService = vertex_ai_search_service.VertexAISearchService


class TestVertexAISearchService:
    """VertexAISearchServiceのテスト。"""

    @pytest.fixture
    def mock_credentials(self) -> MagicMock:
        """モックの認証情報を作成する。"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_credentials: MagicMock) -> VertexAISearchService:
        """テスト用のサービスインスタンスを作成する。"""
        with patch(
            "notebooklm_enterprise_experiments_py.infrastructure.external."
            "vertex_ai_search_service.discoveryengine.ConversationalSearchServiceClient"
        ):
            return VertexAISearchService(
                project_id="test-project",
                location="global",
                engine_id="test-engine",
                credentials=mock_credentials,
            )

    def test_init_with_credentials(self, mock_credentials: MagicMock) -> None:
        """認証情報を指定して初期化できる。"""
        with patch(
            "notebooklm_enterprise_experiments_py.infrastructure.external."
            "vertex_ai_search_service.discoveryengine.ConversationalSearchServiceClient"
        ) as mock_client:
            service = VertexAISearchService(
                project_id="test-project",
                location="global",
                engine_id="test-engine",
                credentials=mock_credentials,
            )
            assert service.project_id == "test-project"
            assert service.location == "global"
            assert service.engine_id == "test-engine"
            mock_client.assert_called_once_with(credentials=mock_credentials)

    def test_build_serving_config_path(
        self, service: VertexAISearchService
    ) -> None:
        """serving_configパスを正しく構築できる。"""
        expected = (
            "projects/test-project/locations/global/"
            "collections/default_collection/engines/test-engine/"
            "servingConfigs/default_serving_config"
        )
        assert service._build_serving_config_path() == expected

    def test_search_and_answer_returns_search_result(
        self, service: VertexAISearchService
    ) -> None:
        """search_and_answerがSearchResultを返す。"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.answer = MagicMock()
        mock_response.answer.answer_text = "テスト回答"
        mock_response.answer.state = 1
        mock_response.answer.answer_skipped_reasons = []
        mock_response.answer.references = []
        mock_response.answer.citations = []

        service.conversational_client.answer_query.return_value = mock_response

        result = service.search_and_answer("テスト質問")

        assert isinstance(result, SearchResult)
        assert result.summary == "テスト回答"
        assert result.citations == []

    def test_search_and_answer_with_citations(
        self, service: VertexAISearchService
    ) -> None:
        """引用付きの検索結果を正しくパースできる。"""
        # モックリファレンスの設定
        mock_doc_info = MagicMock()
        mock_doc_info.uri = "https://example.com/test"
        mock_doc_info.title = "テストページ"

        mock_reference = MagicMock()
        mock_reference.unstructured_document_info = mock_doc_info

        # モックソースの設定
        mock_source = MagicMock()
        mock_source.reference_index = 0

        # モック引用の設定
        mock_citation = MagicMock()
        mock_citation.sources = [mock_source]

        mock_response = MagicMock()
        mock_response.answer = MagicMock()
        mock_response.answer.answer_text = "AIの回答です"
        mock_response.answer.state = 1
        mock_response.answer.answer_skipped_reasons = []
        mock_response.answer.references = [mock_reference]
        mock_response.answer.citations = [mock_citation]

        service.conversational_client.answer_query.return_value = mock_response

        result = service.search_and_answer("質問")

        assert result.summary == "AIの回答です"
        assert len(result.citations) == 1
        assert result.citations[0].title == "テストページ"
        assert result.citations[0].url == "https://example.com/test"

    def test_search_and_answer_without_answer(
        self, service: VertexAISearchService
    ) -> None:
        """回答がない場合は空文字列を返す。"""
        mock_response = MagicMock()
        mock_response.answer = None

        service.conversational_client.answer_query.return_value = mock_response

        result = service.search_and_answer("質問")

        assert result.summary == ""

    def test_load_credentials_without_env(self) -> None:
        """認証情報が設定されていない場合はエラーを発生させる。"""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external."
                "vertex_ai_search_service.get_service_account_key_info",
                return_value=None,
            ),
            patch(
                "notebooklm_enterprise_experiments_py.infrastructure.external."
                "vertex_ai_search_service.get_service_account_key_path",
                return_value=None,
            ),
        ):
            with pytest.raises(
                ValueError, match="サービスアカウント認証情報が設定されていません"
            ):
                VertexAISearchService(
                    project_id="test-project",
                    location="global",
                    engine_id="test-engine",
                )
