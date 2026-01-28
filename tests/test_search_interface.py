"""検索インターフェースのテスト。"""

from notebooklm_enterprise_experiments_py.interfaces.search_interface import (
    ISearchService,
    SearchCitation,
    SearchResult,
)


class TestSearchCitation:
    """SearchCitationのテスト。"""

    def test_create_citation(self) -> None:
        """引用情報を作成できる。"""
        citation = SearchCitation(
            title="テストタイトル",
            url="https://example.com/test",
        )
        assert citation.title == "テストタイトル"
        assert citation.url == "https://example.com/test"

    def test_citation_is_immutable(self) -> None:
        """引用情報はイミュータブルである。"""
        citation = SearchCitation(title="テスト", url="https://example.com")
        try:
            citation.title = "変更後"  # type: ignore[misc]
            assert False, "FrozenInstanceErrorが発生するべき"
        except Exception:
            pass


class TestSearchResult:
    """SearchResultのテスト。"""

    def test_create_result_with_citations(self) -> None:
        """引用付きの検索結果を作成できる。"""
        citations = [
            SearchCitation(title="参照1", url="https://example.com/1"),
            SearchCitation(title="参照2", url="https://example.com/2"),
        ]
        result = SearchResult(
            summary="これはテストの回答です。",
            citations=citations,
        )
        assert result.summary == "これはテストの回答です。"
        assert len(result.citations) == 2
        assert result.citations[0].title == "参照1"

    def test_create_result_without_citations(self) -> None:
        """引用なしの検索結果を作成できる。"""
        result = SearchResult(
            summary="回答テキスト",
            citations=[],
        )
        assert result.summary == "回答テキスト"
        assert len(result.citations) == 0

    def test_result_is_immutable(self) -> None:
        """検索結果はイミュータブルである。"""
        result = SearchResult(summary="テスト", citations=[])
        try:
            result.summary = "変更後"  # type: ignore[misc]
            assert False, "FrozenInstanceErrorが発生するべき"
        except Exception:
            pass


class TestISearchService:
    """ISearchServiceインターフェースのテスト。"""

    def test_is_abstract_class(self) -> None:
        """ISearchServiceは抽象クラスである。"""
        try:
            ISearchService()  # type: ignore[abstract]
            assert False, "TypeErrorが発生するべき"
        except TypeError:
            pass

    def test_concrete_implementation(self) -> None:
        """具象クラスを実装できる。"""

        class ConcreteSearchService(ISearchService):
            def search_and_answer(self, query: str) -> SearchResult:
                return SearchResult(
                    summary=f"クエリ「{query}」に対する回答",
                    citations=[],
                )

        service = ConcreteSearchService()
        result = service.search_and_answer("テスト質問")
        assert "テスト質問" in result.summary
