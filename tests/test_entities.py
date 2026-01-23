"""エンティティのテスト。"""

import pytest

from notebooklm_enterprise_experiments_py.domain.entities.notebook import Notebook
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)


class TestNotebook:
    """Notebookエンティティのテスト。"""

    def test_valid_notebook(self) -> None:
        """有効なNotebookを作成できる。"""
        notebook_id = NotebookId("test-notebook-123")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )
        assert notebook.notebook_id == notebook_id
        assert notebook.display_name == "テストノートブック"
        assert notebook.sources == []

    def test_notebook_with_sources(self) -> None:
        """ソース付きのNotebookを作成できる。"""
        notebook_id = NotebookId("test-notebook-123")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
            sources=["gs://bucket/doc1.pdf", "gs://bucket/doc2.pdf"],
        )
        assert len(notebook.sources) == 2
        assert "gs://bucket/doc1.pdf" in notebook.sources
        assert "gs://bucket/doc2.pdf" in notebook.sources

    def test_empty_display_name_raises_error(self) -> None:
        """空文字列のdisplay_nameはエラーを発生させる。"""
        notebook_id = NotebookId("test-notebook-123")
        with pytest.raises(ValueError, match="display_nameは空文字列にできません"):
            Notebook(
                notebook_id=notebook_id,
                display_name="",
            )

    def test_non_string_display_name_raises_error(self) -> None:
        """文字列以外のdisplay_nameはエラーを発生させる。"""
        notebook_id = NotebookId("test-notebook-123")
        with pytest.raises(ValueError, match="display_nameは文字列である必要があります"):
            Notebook(
                notebook_id=notebook_id,
                display_name=123,  # type: ignore[arg-type]
            )

    def test_non_list_sources_raises_error(self) -> None:
        """リスト以外のsourcesはエラーを発生させる。"""
        notebook_id = NotebookId("test-notebook-123")
        with pytest.raises(ValueError, match="sourcesはリストである必要があります"):
            Notebook(
                notebook_id=notebook_id,
                display_name="テストノートブック",
                sources="invalid",  # type: ignore[arg-type]
            )

    def test_non_string_source_uri_raises_error(self) -> None:
        """文字列以外のソースURIはエラーを発生させる。"""
        notebook_id = NotebookId("test-notebook-123")
        with pytest.raises(ValueError, match="sourcesの要素は文字列である必要があります"):
            Notebook(
                notebook_id=notebook_id,
                display_name="テストノートブック",
                sources=[123],  # type: ignore[list-item]
            )

    def test_add_source(self) -> None:
        """ソースURIを追加できる。"""
        notebook_id = NotebookId("test-notebook-123")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )
        notebook.add_source("gs://bucket/doc1.pdf")
        assert "gs://bucket/doc1.pdf" in notebook.sources

    def test_add_duplicate_source(self) -> None:
        """重複するソースURIは追加されない。"""
        notebook_id = NotebookId("test-notebook-123")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )
        notebook.add_source("gs://bucket/doc1.pdf")
        notebook.add_source("gs://bucket/doc1.pdf")
        assert notebook.sources.count("gs://bucket/doc1.pdf") == 1

    def test_add_non_string_source_raises_error(self) -> None:
        """文字列以外のソースURIはエラーを発生させる。"""
        notebook_id = NotebookId("test-notebook-123")
        notebook = Notebook(
            notebook_id=notebook_id,
            display_name="テストノートブック",
        )
        with pytest.raises(ValueError, match="source_uriは文字列である必要があります"):
            notebook.add_source(123)  # type: ignore[arg-type]
