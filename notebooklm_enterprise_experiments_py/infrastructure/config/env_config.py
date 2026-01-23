"""環境変数の設定と読み込みを行うモジュール。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートディレクトリを取得
# (infrastructure/config/から3階層上がプロジェクトルート)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# .envファイルを読み込む
load_dotenv(PROJECT_ROOT / ".env")


def get_env(key: str, default: str | None = None) -> str | None:
    """
    環境変数を取得する。

    Args:
        key: 環境変数のキー
        default: デフォルト値（環境変数が存在しない場合）

    Returns:
        環境変数の値、またはデフォルト値
    """
    return os.getenv(key, default)


def get_gcp_project_id() -> str:
    """
    GCPプロジェクトIDを取得する。

    Returns:
        GCPプロジェクトID

    Raises:
        ValueError: GCP_PROJECT_IDが設定されていない場合
    """
    project_id = get_env("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError(
            "GCP_PROJECT_ID環境変数が設定されていません。"
            ".envファイルを作成してGCP_PROJECT_IDを設定してください。"
        )
    return project_id


def get_gcp_region(default: str = "us-central1") -> str:
    """
    GCPリージョンを取得する。

    Args:
        default: デフォルトリージョン

    Returns:
        GCPリージョン
    """
    result = get_env("GCP_REGION", default)
    return result if result is not None else default


def get_gcp_location(default: str = "global") -> str:
    """
    GCPロケーションを取得する。

    Args:
        default: デフォルトロケーション

    Returns:
        GCPロケーション
    """
    result = get_env("GCP_LOCATION", default)
    return result if result is not None else default
