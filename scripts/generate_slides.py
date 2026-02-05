#!/usr/bin/env python3
"""検索結果からスライド構成案（Markdown）を生成するスクリプト。

このスクリプトは、Vertex AI Searchで検索・要約した結果を元に、
Gemini Proを使用してプレゼンテーション用のスライド構成を生成する。
出力はMarp互換のMarkdown形式で、ファイルに保存される。

実行方法:
    # デフォルトの出力ファイル名で実行
    python scripts/generate_slides.py "検索クエリ"

    # 出力ファイル名を指定して実行
    python scripts/generate_slides.py "検索クエリ" --output my_slides.md

必要な環境変数:
    - GCP_PROJECT_ID: GCPプロジェクトID
    - ENGINE_ID: 検索アプリ（Engine）のID
    - LOCATION: GCPロケーション（デフォルト: global）
    - GEMINI_MODEL: 使用するGeminiモデル（デフォルト: gemini-2.5-flash）
    - GCP_SERVICE_ACCOUNT_KEY_PATH または GCP_SERVICE_ACCOUNT_KEY_JSON: 認証情報
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from notebooklm_enterprise_experiments_py.config.env_config import (  # noqa: E402
    get_engine_id,
    get_gcp_location,
    get_gcp_project_id,
    get_gemini_model,
)
from notebooklm_enterprise_experiments_py.services.content_generator import (  # noqa: E402
    ContentGenerator,
)
from notebooklm_enterprise_experiments_py.services.vertex_ai_search_service import (  # noqa: E402
    VertexAISearchService,
)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする。"""
    parser = argparse.ArgumentParser(
        description="検索結果からスライド構成案（Markdown）を生成する"
    )
    parser.add_argument(
        "query",
        help="検索クエリ（例: '新入社員向けのセキュリティ研修資料を作って'）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output_slides.md",
        help="出力ファイル名（デフォルト: output_slides.md）",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="使用するGeminiモデル（環境変数GEMINI_MODELまたはgemini-2.5-flash）",
    )
    return parser.parse_args()


def main() -> None:
    """メイン関数。"""
    args = parse_args()

    print("=" * 60)
    print("スライド生成ツール")
    print("=" * 60)
    print()

    # 環境変数の取得
    try:
        project_id = get_gcp_project_id()
        engine_id = get_engine_id()
        location = get_gcp_location()
    except ValueError as e:
        print(f"エラー: {e}")
        print()
        print("必要な環境変数を.envファイルに設定してください。")
        sys.exit(1)

    # モデル名の決定（コマンドライン引数 > 環境変数 > デフォルト）
    model_name = args.model if args.model else get_gemini_model()

    print(f"プロジェクトID: {project_id}")
    print(f"Engine ID: {engine_id}")
    print(f"ロケーション: {location}")
    print(f"使用モデル: {model_name}")
    print()

    # Step 1: 検索サービスの初期化と検索実行
    print("Step 1: ドキュメント検索")
    print("-" * 40)
    print(f"クエリ: {args.query}")
    print()

    try:
        search_service = VertexAISearchService(
            project_id=project_id,
            location=location,
            engine_id=engine_id,
        )
        # 新しいsearch_documentsメソッドを使用（20件取得）
        search_result = search_service.search_documents(args.query)
    except Exception as e:
        print(f"検索エラー: {e}")
        sys.exit(1)

    if not search_result.results:
        print("警告: 検索結果が空です。スライド生成をスキップします。")
        sys.exit(1)

    print(f"【検索結果】{len(search_result.results)}件のドキュメントを取得")
    for i, doc in enumerate(search_result.results[:5], 1):
        print(f"  {i}. {doc.title}")
    if len(search_result.results) > 5:
        print(f"  ... 他{len(search_result.results) - 5}件")
    print()

    # 検索結果からソーステキストを構築
    source_parts = ["【検索結果】"]
    for i, doc in enumerate(search_result.results, 1):
        source_parts.append(f"\n[Document {i}] {doc.title}")
        if doc.content:
            source_parts.append(f"内容: {doc.content}")
        if doc.url:
            source_parts.append(f"URL: {doc.url}")
    source_text = "\n".join(source_parts)

    # Step 2: スライド生成
    print("Step 2: スライド構成生成（Gemini Pro）")
    print("-" * 40)

    try:
        # Gemini用のロケーションは通常 us-central1
        generator = ContentGenerator(
            project_id=project_id,
            location="us-central1",
            model_name=model_name,
        )
        slide_markdown = generator.generate_slide_markdown(source_text)
    except Exception as e:
        print(f"生成エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 3: ファイル保存
    print("Step 3: ファイル保存")
    print("-" * 40)

    output_path = Path(args.output)
    output_path.write_text(slide_markdown, encoding="utf-8")

    print(f"出力ファイル: {output_path.absolute()}")
    print()

    # プレビュー表示
    print("【生成されたMarkdown（プレビュー）】")
    print("-" * 40)
    preview = slide_markdown[:1000]
    if len(slide_markdown) > 1000:
        preview += "\n...(以下省略)"
    print(preview)
    print()

    print("=" * 60)
    print("完了")
    print("=" * 60)
    print()
    print("ヒント: VS Code + Marp拡張機能でプレビューできます")


if __name__ == "__main__":
    main()
