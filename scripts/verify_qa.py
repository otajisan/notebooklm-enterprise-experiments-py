#!/usr/bin/env python3
"""Vertex AI Search (Discovery Engine) の動作検証スクリプト。

このスクリプトは、Vertex AI Searchを使用して
データストアに対する検索と回答生成が正しく動作することを確認する。

実行方法:
    # デフォルトの質問で実行
    python scripts/verify_qa.py

    # カスタムの質問で実行
    python scripts/verify_qa.py "質問内容をここに記述"

必要な環境変数:
    - GCP_PROJECT_ID: GCPプロジェクトID
    - ENGINE_ID: 検索アプリ（Engine）のID
    - LOCATION: GCPロケーション（デフォルト: global）
    - GCP_SERVICE_ACCOUNT_KEY_PATH または GCP_SERVICE_ACCOUNT_KEY_JSON: 認証情報
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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


def main() -> None:
    """検証スクリプトのメイン関数。"""
    print("=" * 60)
    print("Vertex AI Search (Discovery Engine) 動作検証")
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
        print(".env.exampleを参考にしてください。")
        sys.exit(1)

    print(f"プロジェクトID: {project_id}")
    print(f"Engine ID: {engine_id}")
    print(f"ロケーション: {location}")
    print()

    # VertexAISearchServiceの初期化
    print("VertexAISearchService を初期化中...")
    try:
        service = VertexAISearchService(
            project_id=project_id,
            location=location,
            engine_id=engine_id,
        )
        print("初期化完了")
        print()
    except ValueError as e:
        print(f"初期化エラー: {e}")
        sys.exit(1)

    # コマンドライン引数から質問を取得（なければデフォルト）
    default_query = "このデータストアにあるドキュメントの概要を教えてください"
    query = sys.argv[1] if len(sys.argv) > 1 else default_query

    print(f"質問: {query}")
    print("-" * 60)
    print()

    try:
        # Step 0: クエリから検索パラメータを抽出
        print("Step 0: 検索パラメータの抽出")
        print("-" * 40)

        model_name = get_gemini_model()
        print(f"使用モデル: {model_name}")

        generator = ContentGenerator(
            project_id=project_id,
            location="us-central1",
            model_name=model_name,
        )

        search_params = generator.generate_search_params(query)
        search_query = search_params.get("query", query)
        filter_str = search_params.get("filter")
        order_by = search_params.get("order_by")

        print(f"検索クエリ: {search_query}")
        if filter_str:
            print(f"フィルタ: {filter_str}")
        if order_by:
            print(f"ソート: {order_by}")
        print()

        # Step 1: 検索を実行（20件取得）
        print("Step 1: ドキュメント検索")
        print("-" * 40)
        search_result = service.search_documents(
            search_query,
            filter_str=filter_str,
            order_by=order_by,
        )

        if not search_result.results:
            print("検索結果が見つかりませんでした。")
            sys.exit(1)

        print(f"検索結果: {len(search_result.results)}件のドキュメントを取得")
        print()

        # 参照ドキュメントを表示
        print("【参照ドキュメント】")
        for i, doc in enumerate(search_result.results[:10], 1):
            print(f"  {i}. {doc.title}")
            if doc.url:
                print(f"     URL: {doc.url}")
            if doc.content:
                content_preview = doc.content[:200]
                if len(doc.content) > 200:
                    content_preview += "..."
                print(f"     内容: {content_preview}")
            print()

        # Step 2: Geminiで回答を生成
        print("Step 2: 回答生成（Gemini）")
        print("-" * 40)

        # 検索結果を辞書リストに変換
        search_results_dict = [
            {
                "title": doc.title,
                "content": doc.content,
                "url": doc.url,
            }
            for doc in search_result.results
        ]

        answer = generator.generate_answer_from_context(query, search_results_dict)

        # AIの回答を表示
        print()
        print("【AIの回答】")
        print(answer if answer else "(回答なし)")
        print()

        print("=" * 60)
        print("検証完了")
        print("=" * 60)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
