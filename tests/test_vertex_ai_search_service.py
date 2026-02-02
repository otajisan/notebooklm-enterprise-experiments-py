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
            "vertex_ai_search_service.discoveryengine.SearchServiceClient"
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
            "vertex_ai_search_service.discoveryengine.SearchServiceClient"
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
            mock_client.assert_called_once_with(
                credentials=mock_credentials,
                client_options=None,
            )

    def test_init_with_non_global_location(self, mock_credentials: MagicMock) -> None:
        """global以外のlocationでは適切なエンドポイントが設定される。"""
        with patch(
            "notebooklm_enterprise_experiments_py.infrastructure.external."
            "vertex_ai_search_service.discoveryengine.SearchServiceClient"
        ) as mock_client:
            VertexAISearchService(
                project_id="test-project",
                location="us-central1",
                engine_id="test-engine",
                credentials=mock_credentials,
            )
            # client_optionsが設定されていることを確認
            call_kwargs = mock_client.call_args.kwargs
            assert call_kwargs["client_options"] is not None

    def test_serving_config_uses_engines_path(
        self, mock_credentials: MagicMock
    ) -> None:
        """serving_configは/engines/を含むパスを使用する。"""
        with patch(
            "notebooklm_enterprise_experiments_py.infrastructure.external."
            "vertex_ai_search_service.discoveryengine.SearchServiceClient"
        ):
            service = VertexAISearchService(
                project_id="test-project",
                location="global",
                engine_id="test-engine",
                credentials=mock_credentials,
            )
            # /engines/ を含み、/dataStores/ を含まないことを確認
            assert "/engines/test-engine/" in service.serving_config
            assert "/dataStores/" not in service.serving_config
            expected = (
                "projects/test-project/locations/global"
                "/collections/default_collection/engines/test-engine"
                "/servingConfigs/default_serving_config"
            )
            assert service.serving_config == expected

    def test_search_and_answer_returns_search_result(
        self, service: VertexAISearchService
    ) -> None:
        """search_and_answerがSearchResultを返す。"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.summary = MagicMock()
        mock_response.summary.summary_text = "テスト回答"
        mock_response.summary.summary_skipped_reasons = []
        mock_response.results = []

        service.search_client.search.return_value = mock_response

        result = service.search_and_answer("テスト質問")

        assert isinstance(result, SearchResult)
        assert result.summary == "テスト回答"
        assert result.citations == []

    def test_search_and_answer_with_citations(
        self, service: VertexAISearchService
    ) -> None:
        """引用付きの検索結果を正しくパースできる。"""
        # モックドキュメントの設定
        mock_doc = MagicMock()
        mock_doc.derived_struct_data = {
            "title": "テストページ",
            "link": "https://example.com/test",
        }

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_response = MagicMock()
        mock_response.summary = MagicMock()
        mock_response.summary.summary_text = "AIの回答です"
        mock_response.summary.summary_skipped_reasons = []
        mock_response.results = [mock_result]

        service.search_client.search.return_value = mock_response

        result = service.search_and_answer("質問")

        assert result.summary == "AIの回答です"
        assert len(result.citations) == 1
        assert result.citations[0].title == "テストページ"
        assert result.citations[0].url == "https://example.com/test"

    def test_search_and_answer_without_summary(
        self, service: VertexAISearchService
    ) -> None:
        """サマリーがない場合は空文字列を返す。"""
        mock_response = MagicMock()
        mock_response.summary = None
        mock_response.results = []

        service.search_client.search.return_value = mock_response

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
