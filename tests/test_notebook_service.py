"""NotebookServiceのテスト。"""

from unittest.mock import Mock

import pytest

from notebooklm_enterprise_experiments_py.application.dto.notebook_dto import (
    AddSourcesRequest,
    AskRequest,
    CreateNotebookRequest,
)
from notebooklm_enterprise_experiments_py.application.services.notebook_service import (
    NotebookService,
)
from notebooklm_enterprise_experiments_py.domain.entities.notebook import Notebook
from notebooklm_enterprise_experiments_py.domain.repositories.notebook_repository import (
    NotebookRepository,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.answer import (
    Answer,
    Citation,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query


class TestNotebookService:
    """NotebookServiceのテスト。"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックリポジトリを作成する。"""
        return Mock(spec=NotebookRepository)

    @pytest.fixture
    def service(self, mock_repository: Mock) -> NotebookService:
        """NotebookServiceのインスタンスを作成する。"""
        return NotebookService(repository=mock_repository)

    def test_create_notebook(
        self, service: NotebookService, mock_repository: Mock
    ) -> None:
        """ノートブックを作成できる。"""
        notebook_id = NotebookId("test-notebook")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )
        mock_repository.create = Mock(return_value=notebook)

        request = CreateNotebookRequest(
            notebook_id="test-notebook",
            display_name="テストノートブック",
        )
        response = service.create_notebook(request)

        assert response.notebook_id == "test-notebook"
        assert response.display_name == "テストノートブック"
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args
        assert call_args[1]["notebook_id"] == notebook_id
        assert call_args[1]["display_name"] == "テストノートブック"

    def test_add_sources(
        self, service: NotebookService, mock_repository: Mock
    ) -> None:
        """ソースを追加できる。"""
        mock_repository.add_sources = Mock()

        request = AddSourcesRequest(
            notebook_id="test-notebook",
            source_uris=["gs://bucket/doc1.pdf"],
        )
        service.add_sources(request)

        mock_repository.add_sources.assert_called_once()
        call_args = mock_repository.add_sources.call_args
        assert call_args[1]["notebook_id"] == NotebookId("test-notebook")
        assert call_args[1]["source_uris"] == ["gs://bucket/doc1.pdf"]

    def test_ask(self, service: NotebookService, mock_repository: Mock) -> None:
        """質問できる。"""
        citation = Citation(source_title="ドキュメント1", content="内容1")
        answer = Answer(
            answer_text="これは回答です。",
            citations=(citation,),
        )
        mock_repository.ask = Mock(return_value=answer)

        request = AskRequest(
            notebook_id="test-notebook",
            query="最新の売上状況は？",
        )
        response = service.ask(request)

        assert response.answer_text == "これは回答です。"
        assert len(response.citations) == 1
        assert response.citations[0].source_title == "ドキュメント1"
        assert response.citations[0].content == "内容1"
        mock_repository.ask.assert_called_once()
        call_args = mock_repository.ask.call_args
        assert call_args[1]["notebook_id"] == NotebookId("test-notebook")
        assert call_args[1]["query"] == Query("最新の売上状況は？")
