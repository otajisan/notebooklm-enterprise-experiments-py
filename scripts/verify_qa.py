#!/usr/bin/env python3
"""Vertex AI Search (Discovery Engine) の動作検証スクリプト。

このスクリプトは、Vertex AI Searchを使用して
Webサイトデータに対する検索と回答生成が正しく動作することを確認する。

実行方法:
    python scripts/verify_qa.py

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

    # 質問の実行
    query = "スパイスを使った初心者向けのカレーレシピを提案してください"
    print(f"質問: {query}")
    print("-" * 60)
    print()

    try:
        result = service.search_and_answer(query)

        # AIの回答を表示
        print("【AIの回答】")
        print(result.summary if result.summary else "(回答なし)")
        print()

        # 引用元を表示
        print("【根拠となったWebページ】")
        if result.citations:
            for i, citation in enumerate(result.citations, 1):
                print(f"  {i}. {citation.title}")
                print(f"     URL: {citation.url}")
                print()
        else:
            print("  (引用元なし)")
        print()

        print("=" * 60)
        print("検証完了")
        print("=" * 60)

    except Exception as e:
        print(f"検索エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
