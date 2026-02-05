#!/usr/bin/env python3
"""検索結果から図解（Mermaid.js）を生成するスクリプト。

このスクリプトは、Vertex AI Searchで検索・要約した結果を元に、
Gemini Proを使用してMermaid.js形式の図解を生成する。
出力はMermaid記法のMarkdownファイルとして保存される。

実行方法:
    # デフォルトの出力ファイル名で実行
    python scripts/generate_infographic.py "検索クエリ"

    # 出力ファイル名を指定して実行
    python scripts/generate_infographic.py "検索クエリ" --output my_diagram.md

    # 図の種類を指定して実行
    python scripts/generate_infographic.py "検索クエリ" --type sequence

必要な環境変数:
    - GCP_PROJECT_ID: GCPプロジェクトID
    - ENGINE_ID: 検索アプリ（Engine）のID
    - LOCATION: GCPロケーション（デフォルト: global）
    - GEMINI_MODEL: 使用するGeminiモデル（デフォルト: gemini-2.5-flash）
    - GCP_SERVICE_ACCOUNT_KEY_PATH または GCP_SERVICE_ACCOUNT_KEY_JSON: 認証情報

サポートする図の種類:
    - flowchart: フローチャート（デフォルト）
    - sequence: シーケンス図
    - mindmap: マインドマップ
    - classDiagram: クラス図
    - stateDiagram: 状態遷移図
    - erDiagram: ER図
    - gantt: ガントチャート
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

SUPPORTED_CHART_TYPES = [
    "flowchart",
    "sequence",
    "mindmap",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "gantt",
]


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする。"""
    parser = argparse.ArgumentParser(
        description="検索結果から図解（Mermaid.js）を生成する"
    )
    parser.add_argument(
        "query",
        help="検索クエリ（例: '稟議申請のフローチャートを作って'）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output_diagram.md",
        help="出力ファイル名（デフォルト: output_diagram.md）",
    )
    parser.add_argument(
        "--type",
        "-t",
        default="flowchart",
        choices=SUPPORTED_CHART_TYPES,
        help="図の種類（デフォルト: flowchart）",
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
    print("図解生成ツール（Mermaid.js）")
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
    print(f"図の種類: {args.type}")
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
        print("警告: 検索結果が空です。図解生成をスキップします。")
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

    # Step 2: 図解生成
    print("Step 2: 図解生成（Gemini Pro）")
    print("-" * 40)

    try:
        # Gemini用のロケーションは通常 us-central1
        generator = ContentGenerator(
            project_id=project_id,
            location="us-central1",
            model_name=model_name,
        )
        mermaid_code = generator.generate_infographic_code(
            source_text, chart_type=args.type
        )
    except Exception as e:
        print(f"生成エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 3: ファイル保存
    print("Step 3: ファイル保存")
    print("-" * 40)

    output_path = Path(args.output)
    output_path.write_text(mermaid_code, encoding="utf-8")

    print(f"出力ファイル: {output_path.absolute()}")
    print()

    # プレビュー表示
    print("【生成されたMermaidコード】")
    print("-" * 40)
    print(mermaid_code)
    print()

    print("=" * 60)
    print("完了")
    print("=" * 60)
    print()
    print("ヒント:")
    print("  - VS Code + Mermaid拡張機能でプレビューできます")
    print("  - GitHub/GitLabのMarkdownでも直接表示できます")
    print("  - https://mermaid.live/ でオンラインプレビューできます")


if __name__ == "__main__":
    main()
