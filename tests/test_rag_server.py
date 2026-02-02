"""MCPサーバー（rag_server）のテスト。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# servers モジュールのインポートパスを設定
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from notebooklm_enterprise_experiments_py.interfaces.search_interface import (  # noqa: E402
    SearchCitation,
    SearchResult,
)
from servers import rag_server  # noqa: E402


class TestListTools:
    """list_toolsのテスト。"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_three_tools(self) -> None:
        """3つのツールが定義されている。"""
        tools = await rag_server.list_tools()
        assert len(tools) == 3

    @pytest.mark.asyncio
    async def test_list_tools_contains_search_documents(self) -> None:
        """search_documentsツールが含まれる。"""
        tools = await rag_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "search_documents" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_generate_slide_draft(self) -> None:
        """generate_slide_draftツールが含まれる。"""
        tools = await rag_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "generate_slide_draft" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_generate_diagram(self) -> None:
        """generate_diagramツールが含まれる。"""
        tools = await rag_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "generate_diagram" in tool_names


class TestSearchDocuments:
    """_search_documentsのテスト。"""

    @pytest.mark.asyncio
    async def test_search_documents_returns_result(self) -> None:
        """検索結果を返す。"""
        mock_result = SearchResult(
            summary="テスト要約",
            citations=[
                SearchCitation(title="ドキュメント1", url="https://example.com/doc1"),
            ],
        )

        with patch.object(rag_server, "_get_search_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_and_answer.return_value = mock_result
            mock_get_service.return_value = mock_service

            result = await rag_server._search_documents({"query": "テストクエリ"})

            assert len(result) == 1
            assert "テスト要約" in result[0].text
            assert "ドキュメント1" in result[0].text

    @pytest.mark.asyncio
    async def test_search_documents_without_query(self) -> None:
        """queryパラメータがない場合はエラーを返す。"""
        result = await rag_server._search_documents({})
        assert "エラー" in result[0].text

    @pytest.mark.asyncio
    async def test_search_documents_handles_exception(self) -> None:
        """例外発生時はエラーメッセージを返す。"""
        with patch.object(rag_server, "_get_search_service") as mock_get_service:
            mock_get_service.side_effect = Exception("テストエラー")

            result = await rag_server._search_documents({"query": "テスト"})

            assert "検索エラー" in result[0].text


class TestGenerateSlideDraft:
    """_generate_slide_draftのテスト。"""

    @pytest.mark.asyncio
    async def test_generate_slide_draft_returns_markdown(self) -> None:
        """スライドMarkdownを返す。"""
        mock_search_result = SearchResult(
            summary="テスト要約",
            citations=[SearchCitation(title="ドキュメント", url="https://example.com")],
        )

        with (
            patch.object(rag_server, "_get_search_service") as mock_get_search,
            patch.object(rag_server, "_get_content_generator") as mock_get_generator,
        ):
            mock_search = MagicMock()
            mock_search.search_and_answer.return_value = mock_search_result
            mock_get_search.return_value = mock_search

            mock_generator = MagicMock()
            mock_generator.generate_slide_markdown.return_value = """---
marp: true
---
# タイトル
"""
            mock_get_generator.return_value = mock_generator

            result = await rag_server._generate_slide_draft({"query": "テストテーマ"})

            assert "marp: true" in result[0].text

    @pytest.mark.asyncio
    async def test_generate_slide_draft_without_query(self) -> None:
        """queryパラメータがない場合はエラーを返す。"""
        result = await rag_server._generate_slide_draft({})
        assert "エラー" in result[0].text

    @pytest.mark.asyncio
    async def test_generate_slide_draft_no_search_result(self) -> None:
        """検索結果がない場合はスキップメッセージを返す。"""
        mock_search_result = SearchResult(summary="", citations=[])

        with patch.object(rag_server, "_get_search_service") as mock_get_search:
            mock_search = MagicMock()
            mock_search.search_and_answer.return_value = mock_search_result
            mock_get_search.return_value = mock_search

            result = await rag_server._generate_slide_draft({"query": "テスト"})

            assert "検索結果が見つかりませんでした" in result[0].text


class TestGenerateDiagram:
    """_generate_diagramのテスト。"""

    @pytest.mark.asyncio
    async def test_generate_diagram_returns_mermaid(self) -> None:
        """Mermaidコードを返す。"""
        mock_search_result = SearchResult(
            summary="テスト要約",
            citations=[],
        )

        with (
            patch.object(rag_server, "_get_search_service") as mock_get_search,
            patch.object(rag_server, "_get_content_generator") as mock_get_generator,
        ):
            mock_search = MagicMock()
            mock_search.search_and_answer.return_value = mock_search_result
            mock_get_search.return_value = mock_search

            mock_generator = MagicMock()
            mock_generator.generate_infographic_code.return_value = """```mermaid
flowchart TD
    A[開始] --> B[終了]
```"""
            mock_get_generator.return_value = mock_generator

            result = await rag_server._generate_diagram({"query": "フロー図"})

            assert "```mermaid" in result[0].text
            assert "flowchart" in result[0].text

    @pytest.mark.asyncio
    async def test_generate_diagram_with_chart_type(self) -> None:
        """chart_typeパラメータが渡される。"""
        mock_search_result = SearchResult(summary="テスト要約", citations=[])

        with (
            patch.object(rag_server, "_get_search_service") as mock_get_search,
            patch.object(rag_server, "_get_content_generator") as mock_get_generator,
        ):
            mock_search = MagicMock()
            mock_search.search_and_answer.return_value = mock_search_result
            mock_get_search.return_value = mock_search

            mock_generator = MagicMock()
            mock_generator.generate_infographic_code.return_value = "```mermaid\n```"
            mock_get_generator.return_value = mock_generator

            await rag_server._generate_diagram(
                {"query": "シーケンス図", "chart_type": "sequence"}
            )

            mock_generator.generate_infographic_code.assert_called_once_with(
                "テスト要約", "sequence"
            )

    @pytest.mark.asyncio
    async def test_generate_diagram_without_query(self) -> None:
        """queryパラメータがない場合はエラーを返す。"""
        result = await rag_server._generate_diagram({})
        assert "エラー" in result[0].text

    @pytest.mark.asyncio
    async def test_generate_diagram_no_search_result(self) -> None:
        """検索結果がない場合はスキップメッセージを返す。"""
        mock_search_result = SearchResult(summary="", citations=[])

        with patch.object(rag_server, "_get_search_service") as mock_get_search:
            mock_search = MagicMock()
            mock_search.search_and_answer.return_value = mock_search_result
            mock_get_search.return_value = mock_search

            result = await rag_server._generate_diagram({"query": "テスト"})

            assert "検索結果が見つかりませんでした" in result[0].text


class TestCallTool:
    """call_toolのテスト。"""

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self) -> None:
        """未知のツール名でエラーを発生させる。"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await rag_server.call_tool("unknown_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_search_documents(self) -> None:
        """search_documentsにルーティングされる。"""
        with patch.object(rag_server, "_search_documents") as mock_search:
            mock_search.return_value = []
            await rag_server.call_tool("search_documents", {"query": "test"})
            mock_search.assert_called_once_with({"query": "test"})

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_generate_slide_draft(self) -> None:
        """generate_slide_draftにルーティングされる。"""
        with patch.object(rag_server, "_generate_slide_draft") as mock_slide:
            mock_slide.return_value = []
            await rag_server.call_tool("generate_slide_draft", {"query": "test"})
            mock_slide.assert_called_once_with({"query": "test"})

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_generate_diagram(self) -> None:
        """generate_diagramにルーティングされる。"""
        with patch.object(rag_server, "_generate_diagram") as mock_diagram:
            mock_diagram.return_value = []
            await rag_server.call_tool("generate_diagram", {"query": "test"})
            mock_diagram.assert_called_once_with({"query": "test"})
