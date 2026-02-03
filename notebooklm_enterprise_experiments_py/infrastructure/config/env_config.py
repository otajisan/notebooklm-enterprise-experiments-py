"""環境変数の設定と読み込みを行うモジュール。"""

import json
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

    LOCATION環境変数を優先的に確認し、存在しない場合はGCP_LOCATIONを使用する。

    Args:
        default: デフォルトロケーション

    Returns:
        GCPロケーション
    """
    # まずLOCATION環境変数を確認（Issue #9の仕様に合わせる）
    result = get_env("LOCATION")
    if result:
        return result
    # 次にGCP_LOCATION環境変数を確認
    result = get_env("GCP_LOCATION", default)
    return result if result is not None else default


def get_service_account_key_path() -> str | None:
    """
    サービスアカウントキーのファイルパスを取得する。

    Returns:
        サービスアカウントキーのファイルパス、またはNone
    """
    return get_env("GCP_SERVICE_ACCOUNT_KEY_PATH")


def get_engine_id() -> str:
    """
    Engine ID（検索アプリID）を取得する。

    Returns:
        Engine ID

    Raises:
        ValueError: ENGINE_IDが設定されていない場合
    """
    engine_id = get_env("ENGINE_ID")
    if not engine_id:
        raise ValueError(
            "ENGINE_ID環境変数が設定されていません。"
            ".envファイルを作成してENGINE_IDを設定してください。"
        )
    return engine_id


def get_service_account_key_info() -> dict | None:
    """
    サービスアカウントキーの情報を辞書として取得する。

    環境変数GCP_SERVICE_ACCOUNT_KEY_JSONにJSON文字列が設定されている場合、
    それをパースして返す。

    Returns:
        サービスアカウントキーの情報を表す辞書、またはNone
    """
    key_json = get_env("GCP_SERVICE_ACCOUNT_KEY_JSON")
    if key_json:
        try:
            return json.loads(key_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"GCP_SERVICE_ACCOUNT_KEY_JSONの形式が不正です: {e}"
            ) from e
    return None


def get_gemini_model(default: str = "gemini-2.5-flash") -> str:
    """
    Geminiモデル名を取得する。

    Args:
        default: デフォルトのモデル名

    Returns:
        Geminiモデル名
    """
    result = get_env("GEMINI_MODEL", default)
    return result if result is not None else default


def get_gcs_bucket_name() -> str | None:
    """
    GCSバケット名を取得する。

    Returns:
        GCSバケット名、またはNone
    """
    return get_env("GCS_BUCKET_NAME")
