#!/usr/bin/env python3
"""Vertex AI機能を統合したMCPサーバー。

このサーバーは、Vertex AI Searchによる検索、スライド生成、図解生成の
3つの機能をMCP (Model Context Protocol) ツールとして公開する。

起動方法:
    uv run python servers/rag_server.py

対応クライアント:
    - Cursor
    - Claude Desktop
    - その他MCP対応AIクライアント
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (  # noqa: E402
    get_engine_id,
    get_gcp_location,
    get_gcp_project_id,
    get_gemini_model,
)
from notebooklm_enterprise_experiments_py.infrastructure.external.content_generator import (  # noqa: E402, E501
    ContentGenerator,
)
from notebooklm_enterprise_experiments_py.infrastructure.external.vertex_ai_search_service import (  # noqa: E402, E501
    VertexAISearchService,
)

# MCPサーバーインスタンスの作成
server = Server("rag-server")


def _get_search_service() -> VertexAISearchService:
    """VertexAISearchServiceのインスタンスを取得する。"""
    project_id = get_gcp_project_id()
    location = get_gcp_location()
    engine_id = get_engine_id()

    return VertexAISearchService(
        project_id=project_id,
        location=location,
        engine_id=engine_id,
    )


def _get_content_generator() -> ContentGenerator:
    """ContentGeneratorのインスタンスを取得する。"""
    project_id = get_gcp_project_id()
    model_name = get_gemini_model()

    return ContentGenerator(
        project_id=project_id,
        location="us-central1",
        model_name=model_name,
    )


@server.list_tools()
async def list_tools() -> list[Tool]:
    """利用可能なツールの一覧を返す。"""
    return [
        Tool(
            name="search_documents",
            description="社内ドキュメント（PDF/Googleドライブ）を検索し、要約と引用元を返す。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワードや質問内容",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="generate_slide_draft",
            description="指定されたトピックや検索結果に基づき、スライド構成案（Markdown）を生成する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "スライドのテーマ",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="generate_diagram",
            description="指定されたトピックに基づき、図解（フローチャート等）のMermaidコードを生成する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "図解したい内容",
                    },
                    "chart_type": {
                        "type": "string",
                        "description": "図の種類",
                        "default": "flowchart",
                        "enum": [
                            "flowchart",
                            "sequence",
                            "mindmap",
                            "classDiagram",
                            "stateDiagram",
                            "erDiagram",
                            "gantt",
                        ],
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """ツールを実行する。"""
    if name == "search_documents":
        return await _search_documents(arguments)
    elif name == "generate_slide_draft":
        return await _generate_slide_draft(arguments)
    elif name == "generate_diagram":
        return await _generate_diagram(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _search_documents(arguments: dict) -> list[TextContent]:
    """ドキュメント検索を実行する。"""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="エラー: queryパラメータが必要です。")]

    try:
        search_service = _get_search_service()
        result = search_service.search_and_answer(query)

        # 結果をフォーマット
        output_parts = []
        output_parts.append("## 検索結果")
        output_parts.append("")

        if result.summary:
            output_parts.append("### 要約")
            output_parts.append(result.summary)
            output_parts.append("")

        if result.citations:
            output_parts.append("### 参照ドキュメント")
            for i, citation in enumerate(result.citations, 1):
                output_parts.append(f"{i}. **{citation.title}**")
                if citation.url:
                    output_parts.append(f"   - URL: {citation.url}")
            output_parts.append("")

        if not result.summary and not result.citations:
            output_parts.append("検索結果が見つかりませんでした。")

        return [TextContent(type="text", text="\n".join(output_parts))]

    except Exception as e:
        return [TextContent(type="text", text=f"検索エラー: {e!s}")]


async def _generate_slide_draft(arguments: dict) -> list[TextContent]:
    """スライド構成案を生成する。"""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="エラー: queryパラメータが必要です。")]

    try:
        # Step 1: 検索を実行
        search_service = _get_search_service()
        search_result = search_service.search_and_answer(query)

        if not search_result.summary:
            return [
                TextContent(
                    type="text",
                    text="検索結果が見つかりませんでした。スライド生成をスキップします。",
                )
            ]

        # 検索結果と引用元を組み合わせてソーステキストを作成
        source_text = f"【要約】\n{search_result.summary}\n\n【参照ドキュメント】\n"
        for i, citation in enumerate(search_result.citations, 1):
            source_text += f"{i}. {citation.title}\n   URL: {citation.url}\n"

        # Step 2: スライド生成
        generator = _get_content_generator()
        slide_markdown = generator.generate_slide_markdown(source_text)

        return [TextContent(type="text", text=slide_markdown)]

    except Exception as e:
        return [TextContent(type="text", text=f"スライド生成エラー: {e!s}")]


async def _generate_diagram(arguments: dict) -> list[TextContent]:
    """図解（Mermaidコード）を生成する。"""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="エラー: queryパラメータが必要です。")]

    chart_type = arguments.get("chart_type", "flowchart")

    try:
        # Step 1: 検索を実行
        search_service = _get_search_service()
        search_result = search_service.search_and_answer(query)

        if not search_result.summary:
            return [
                TextContent(
                    type="text",
                    text="検索結果が見つかりませんでした。図解生成をスキップします。",
                )
            ]

        # Step 2: 図解生成
        generator = _get_content_generator()
        mermaid_code = generator.generate_infographic_code(
            search_result.summary, chart_type
        )

        return [TextContent(type="text", text=mermaid_code)]

    except Exception as e:
        return [TextContent(type="text", text=f"図解生成エラー: {e!s}")]


async def main() -> None:
    """MCPサーバーを起動する。"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
