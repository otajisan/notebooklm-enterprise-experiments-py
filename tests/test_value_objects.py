"""値オブジェクトのテスト。"""

import pytest

from notebooklm_enterprise_experiments_py.domain.value_objects.answer import (
    Answer,
    Citation,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query


class TestNotebookId:
    """NotebookId値オブジェクトのテスト。"""

    def test_valid_notebook_id(self) -> None:
        """有効なNotebookIdを作成できる。"""
        notebook_id = NotebookId("test-notebook-123")
        assert notebook_id.value == "test-notebook-123"
        assert str(notebook_id) == "test-notebook-123"

    def test_empty_notebook_id_raises_error(self) -> None:
        """空文字列のNotebookIdはエラーを発生させる。"""
        with pytest.raises(ValueError, match="NotebookIdは空文字列にできません"):
            NotebookId("")

    def test_non_string_notebook_id_raises_error(self) -> None:
        """文字列以外のNotebookIdはエラーを発生させる。"""
        with pytest.raises(ValueError, match="NotebookIdは文字列である必要があります"):
            NotebookId(123)  # type: ignore[arg-type]


class TestQuery:
    """Query値オブジェクトのテスト。"""

    def test_valid_query(self) -> None:
        """有効なQueryを作成できる。"""
        query = Query("最新の売上状況は？")
        assert query.text == "最新の売上状況は？"
        assert str(query) == "最新の売上状況は？"

    def test_empty_query_raises_error(self) -> None:
        """空文字列のQueryはエラーを発生させる。"""
        with pytest.raises(ValueError, match="Queryは空文字列にできません"):
            Query("")

    def test_non_string_query_raises_error(self) -> None:
        """文字列以外のQueryはエラーを発生させる。"""
        with pytest.raises(ValueError, match="Queryは文字列である必要があります"):
            Query(123)  # type: ignore[arg-type]


class TestCitation:
    """Citation値オブジェクトのテスト。"""

    def test_valid_citation(self) -> None:
        """有効なCitationを作成できる。"""
        citation = Citation(
            source_title="技術ドキュメント",
            content="住宅手当の申請期限は月末までです。",
        )
        assert citation.source_title == "技術ドキュメント"
        assert citation.content == "住宅手当の申請期限は月末までです。"

    def test_non_string_source_title_raises_error(self) -> None:
        """文字列以外のsource_titleはエラーを発生させる。"""
        with pytest.raises(
            ValueError, match="source_titleは文字列である必要があります"
        ):
            Citation(
                source_title=123,  # type: ignore[arg-type]
                content="test",
            )

    def test_non_string_content_raises_error(self) -> None:
        """文字列以外のcontentはエラーを発生させる。"""
        with pytest.raises(ValueError, match="contentは文字列である必要があります"):
            Citation(
                source_title="test",
                content=123,  # type: ignore[arg-type]
            )


class TestAnswer:
    """Answer値オブジェクトのテスト。"""

    def test_valid_answer_without_citations(self) -> None:
        """引用なしの有効なAnswerを作成できる。"""
        answer = Answer(answer_text="これは回答です。")
        assert answer.answer_text == "これは回答です。"
        assert answer.citations == ()
        assert str(answer) == "これは回答です。"

    def test_valid_answer_with_citations(self) -> None:
        """引用ありの有効なAnswerを作成できる。"""
        citation1 = Citation(source_title="ドキュメント1", content="内容1")
        citation2 = Citation(source_title="ドキュメント2", content="内容2")
        answer = Answer(
            answer_text="これは回答です。",
            citations=(citation1, citation2),
        )
        assert answer.answer_text == "これは回答です。"
        assert len(answer.citations) == 2
        assert answer.citations[0] == citation1
        assert answer.citations[1] == citation2

    def test_non_string_answer_text_raises_error(self) -> None:
        """文字列以外のanswer_textはエラーを発生させる。"""
        with pytest.raises(ValueError, match="answer_textは文字列である必要があります"):
            Answer(answer_text=123)  # type: ignore[arg-type]

    def test_non_tuple_citations_raises_error(self) -> None:
        """タプル以外のcitationsはエラーを発生させる。"""
        with pytest.raises(ValueError, match="citationsはタプルである必要があります"):
            Answer(
                answer_text="test",
                citations=[],  # type: ignore[arg-type]
            )

    def test_invalid_citation_type_raises_error(self) -> None:
        """Citation以外の要素を含むcitationsはエラーを発生させる。"""
        with pytest.raises(
            ValueError, match="citationsの要素はCitationである必要があります"
        ):
            Answer(
                answer_text="test",
                citations=("invalid",),  # type: ignore[arg-type]
            )
