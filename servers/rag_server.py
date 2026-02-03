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
    """ドキュメント検索を実行し、Geminiで回答を生成する。"""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="エラー: queryパラメータが必要です。")]

    try:
        # Step 0: クエリから検索パラメータを抽出（日付フィルタ・ソート）
        generator = _get_content_generator()
        search_params = generator.generate_search_params(query)

        search_query = search_params.get("query", query)
        filter_str = search_params.get("filter")
        order_by = search_params.get("order_by")

        # Step 1: 検索を実行（20件取得）
        search_service = _get_search_service()
        search_result = search_service.search_documents(
            search_query,
            filter_str=filter_str,
            order_by=order_by,
        )

        if not search_result.results:
            return [TextContent(type="text", text="検索結果が見つかりませんでした。")]

        # Step 2: 検索結果を辞書リストに変換
        search_results_dict = [
            {
                "title": doc.title,
                "content": doc.content,
                "url": doc.url,
            }
            for doc in search_result.results
        ]

        # Step 3: Geminiで回答を生成
        answer = generator.generate_answer_from_context(query, search_results_dict)

        # 結果をフォーマット
        output_parts = []
        output_parts.append("## 回答")
        output_parts.append("")
        output_parts.append(answer)
        output_parts.append("")
        output_parts.append("---")
        output_parts.append("")

        # フィルタ情報を表示（設定されている場合）
        if filter_str or order_by:
            output_parts.append("### 検索条件")
            if filter_str:
                output_parts.append(f"- フィルタ: {filter_str}")
            if order_by:
                output_parts.append(f"- ソート: {order_by}")
            output_parts.append("")

        output_parts.append("### 参照ドキュメント")
        for i, doc in enumerate(search_result.results[:10], 1):  # 上位10件を表示
            output_parts.append(f"{i}. **{doc.title}**")
            if doc.url:
                output_parts.append(f"   - URL: {doc.url}")
        output_parts.append("")

        return [TextContent(type="text", text="\n".join(output_parts))]

    except Exception as e:
        return [TextContent(type="text", text=f"検索エラー: {e!s}")]


async def _generate_slide_draft(arguments: dict) -> list[TextContent]:
    """スライド構成案を生成する。"""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="エラー: queryパラメータが必要です。")]

    try:
        # Step 0: クエリから検索パラメータを抽出（日付フィルタ・ソート）
        generator = _get_content_generator()
        search_params = generator.generate_search_params(query)

        search_query = search_params.get("query", query)
        filter_str = search_params.get("filter")
        order_by = search_params.get("order_by")

        # Step 1: 検索を実行（20件取得）
        search_service = _get_search_service()
        search_result = search_service.search_documents(
            search_query,
            filter_str=filter_str,
            order_by=order_by,
        )

        if not search_result.results:
            return [
                TextContent(
                    type="text",
                    text="検索結果が見つかりませんでした。スライド生成をスキップします。",
                )
            ]

        # Step 2: 検索結果からソーステキストを構築
        source_parts = ["【検索結果】"]
        for i, doc in enumerate(search_result.results, 1):
            source_parts.append(f"\n[Document {i}] {doc.title}")
            if doc.content:
                source_parts.append(f"内容: {doc.content}")
            if doc.url:
                source_parts.append(f"URL: {doc.url}")
        source_text = "\n".join(source_parts)

        # Step 3: スライド生成
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
        # Step 0: クエリから検索パラメータを抽出（日付フィルタ・ソート）
        generator = _get_content_generator()
        search_params = generator.generate_search_params(query)

        search_query = search_params.get("query", query)
        filter_str = search_params.get("filter")
        order_by = search_params.get("order_by")

        # Step 1: 検索を実行（20件取得）
        search_service = _get_search_service()
        search_result = search_service.search_documents(
            search_query,
            filter_str=filter_str,
            order_by=order_by,
        )

        if not search_result.results:
            return [
                TextContent(
                    type="text",
                    text="検索結果が見つかりませんでした。図解生成をスキップします。",
                )
            ]

        # Step 2: 検索結果からソーステキストを構築
        source_parts = []
        for doc in search_result.results:
            if doc.content:
                source_parts.append(doc.content)
        source_text = "\n\n".join(source_parts)

        # Step 3: 図解生成
        mermaid_code = generator.generate_infographic_code(source_text, chart_type)

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
