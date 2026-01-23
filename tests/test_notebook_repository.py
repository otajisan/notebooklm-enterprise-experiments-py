"""NotebookRepositoryのテスト。"""

from unittest.mock import MagicMock, Mock

import pytest

from notebooklm_enterprise_experiments_py.domain.entities.notebook import Notebook
from notebooklm_enterprise_experiments_py.domain.repositories import (
    NotebookRepository,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.answer import (
    Answer,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query
from notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client import (  # noqa: E501
    NotebookLMClient,
)
from notebooklm_enterprise_experiments_py.infrastructure.repositories import (  # noqa: E501
    NotebookRepositoryImpl,
)


class TestNotebookRepositoryImpl:
    """NotebookRepositoryImplのテスト。"""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """モッククライアントを作成する。"""
        return Mock(spec=NotebookLMClient)

    @pytest.fixture
    def repository(self, mock_client: Mock) -> NotebookRepositoryImpl:
        """NotebookRepositoryImplのインスタンスを作成する。"""
        return NotebookRepositoryImpl(client=mock_client)

    def test_create(
        self, repository: NotebookRepositoryImpl, mock_client: Mock
    ) -> None:
        """ノートブックを作成できる。"""
        mock_response = Mock()
        mock_client.create_notebook = MagicMock(return_value=mock_response)

        notebook_id = NotebookId("test-notebook")
        notebook = repository.create(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )

        assert isinstance(notebook, Notebook)
        assert notebook.notebook_id == notebook_id
        assert notebook.display_name == "テストノートブック"
        mock_client.create_notebook.assert_called_once_with(
            notebook_id="test-notebook",
            display_name="テストノートブック",
        )

    def test_add_sources(
        self, repository: NotebookRepositoryImpl, mock_client: Mock
    ) -> None:
        """ソースを追加できる。"""
        mock_operation = Mock()
        mock_operation.result = MagicMock(return_value=None)
        mock_client.add_sources = MagicMock()

        notebook_id = NotebookId("test-notebook")
        repository.add_sources(
            notebook_id=notebook_id,
            source_uris=["gs://bucket/doc1.pdf"],
        )

        mock_client.add_sources.assert_called_once_with(
            notebook_id="test-notebook",
            source_uris=["gs://bucket/doc1.pdf"],
        )

    def test_ask(self, repository: NotebookRepositoryImpl, mock_client: Mock) -> None:
        """質問できる。"""
        mock_citation = Mock()
        mock_citation.source_title = "ドキュメント1"
        mock_citation.content = "内容1"
        mock_answer = Mock()
        mock_answer.answer_text = "これは回答です。"
        mock_answer.citations = [mock_citation]
        mock_response = Mock()
        mock_response.answer = mock_answer
        mock_client.ask = MagicMock(return_value=mock_response)

        notebook_id = NotebookId("test-notebook")
        query = Query("最新の売上状況は？")
        answer = repository.ask(notebook_id=notebook_id, query=query)

        assert isinstance(answer, Answer)
        assert answer.answer_text == "これは回答です。"
        assert len(answer.citations) == 1
        assert answer.citations[0].source_title == "ドキュメント1"
        assert answer.citations[0].content == "内容1"
        mock_client.ask.assert_called_once_with(
            notebook_id="test-notebook",
            query_text="最新の売上状況は？",
            include_citations=True,
        )


class TestNotebookRepository:
    """NotebookRepositoryインターフェースのテスト。"""

    def test_notebook_repository_is_abstract(self) -> None:
        """NotebookRepositoryは抽象クラスである。"""
        with pytest.raises(TypeError):
            NotebookRepository()  # type: ignore[abstract]
