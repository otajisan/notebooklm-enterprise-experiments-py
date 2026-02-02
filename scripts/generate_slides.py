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
    - GCP_SERVICE_ACCOUNT_KEY_PATH または GCP_SERVICE_ACCOUNT_KEY_JSON: 認証情報
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (  # noqa: E402
    get_engine_id,
    get_gcp_location,
    get_gcp_project_id,
)
from notebooklm_enterprise_experiments_py.infrastructure.external.content_generator import (  # noqa: E402, E501
    ContentGenerator,
)
from notebooklm_enterprise_experiments_py.infrastructure.external.vertex_ai_search_service import (  # noqa: E402, E501
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
        default="gemini-1.5-pro",
        help="使用するGeminiモデル（デフォルト: gemini-1.5-pro）",
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

    print(f"プロジェクトID: {project_id}")
    print(f"Engine ID: {engine_id}")
    print(f"ロケーション: {location}")
    print(f"使用モデル: {args.model}")
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
        search_result = search_service.search_and_answer(args.query)
    except Exception as e:
        print(f"検索エラー: {e}")
        sys.exit(1)

    if not search_result.summary:
        print("警告: 検索結果が空です。スライド生成をスキップします。")
        sys.exit(1)

    print("【検索結果サマリー】")
    summary = search_result.summary
    if len(summary) > 500:
        print(summary[:500] + "...")
    else:
        print(summary)
    print()

    # 検索結果と引用元を組み合わせてソーステキストを作成
    source_text = f"【要約】\n{search_result.summary}\n\n【参照ドキュメント】\n"
    for i, citation in enumerate(search_result.citations, 1):
        source_text += f"{i}. {citation.title}\n   URL: {citation.url}\n"

    # Step 2: スライド生成
    print("Step 2: スライド構成生成（Gemini Pro）")
    print("-" * 40)

    try:
        # Gemini用のロケーションは通常 us-central1
        generator = ContentGenerator(
            project_id=project_id,
            location="us-central1",
            model_name=args.model,
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
