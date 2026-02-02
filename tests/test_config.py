"""設定管理モジュールのテスト。"""

import json
import os
from unittest.mock import patch

import pytest

from notebooklm_enterprise_experiments_py.infrastructure.config import env_config


class TestServiceAccountKey:
    """サービスアカウントキー関連のテスト。"""

    def test_get_service_account_key_path_with_env(self) -> None:
        """環境変数からサービスアカウントキーパスを取得できる。"""
        with patch.dict(
            os.environ, {"GCP_SERVICE_ACCOUNT_KEY_PATH": "/path/to/key.json"}
        ):
            result = env_config.get_service_account_key_path()
            assert result == "/path/to/key.json"

    def test_get_service_account_key_path_without_env(self) -> None:
        """環境変数が設定されていない場合はNoneを返す。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_service_account_key_path()
            assert result is None

    def test_get_service_account_key_info_with_valid_json(self) -> None:
        """有効なJSON文字列からサービスアカウントキー情報を取得できる。"""
        key_info = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
        }
        with patch.dict(
            os.environ,
            {"GCP_SERVICE_ACCOUNT_KEY_JSON": json.dumps(key_info)},
        ):
            result = env_config.get_service_account_key_info()
            assert result == key_info

    def test_get_service_account_key_info_with_invalid_json(self) -> None:
        """無効なJSON文字列はエラーを発生させる。"""
        with patch.dict(os.environ, {"GCP_SERVICE_ACCOUNT_KEY_JSON": "invalid json"}):
            with pytest.raises(
                ValueError, match="GCP_SERVICE_ACCOUNT_KEY_JSONの形式が不正です"
            ):
                env_config.get_service_account_key_info()

    def test_get_service_account_key_info_without_env(self) -> None:
        """環境変数が設定されていない場合はNoneを返す。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_service_account_key_info()
            assert result is None


class TestEngineId:
    """ENGINE_ID関連のテスト。"""

    def test_get_engine_id_with_env(self) -> None:
        """環境変数からENGINE_IDを取得できる。"""
        with patch.dict(os.environ, {"ENGINE_ID": "test-engine-123"}):
            result = env_config.get_engine_id()
            assert result == "test-engine-123"

    def test_get_engine_id_without_env(self) -> None:
        """環境変数が設定されていない場合はエラーを発生させる。"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="ENGINE_ID環境変数が設定されていません"
            ):
                env_config.get_engine_id()


class TestGcpLocation:
    """GCPロケーション関連のテスト。"""

    def test_get_gcp_location_with_location_env(self) -> None:
        """LOCATION環境変数を優先的に使用する。"""
        with patch.dict(
            os.environ, {"LOCATION": "us-central1", "GCP_LOCATION": "global"}
        ):
            result = env_config.get_gcp_location()
            assert result == "us-central1"

    def test_get_gcp_location_with_gcp_location_env(self) -> None:
        """LOCATIONがない場合はGCP_LOCATIONを使用する。"""
        with patch.dict(os.environ, {"GCP_LOCATION": "asia-northeast1"}, clear=True):
            result = env_config.get_gcp_location()
            assert result == "asia-northeast1"

    def test_get_gcp_location_with_default(self) -> None:
        """環境変数が設定されていない場合はデフォルト値を返す。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_gcp_location()
            assert result == "global"

    def test_get_gcp_location_with_custom_default(self) -> None:
        """カスタムデフォルト値を指定できる。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_gcp_location(default="europe-west1")
            assert result == "europe-west1"


class TestGeminiModel:
    """Geminiモデル関連のテスト。"""

    def test_get_gemini_model_with_env(self) -> None:
        """環境変数からGEMINI_MODELを取得できる。"""
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-1.0-pro"}, clear=True):
            result = env_config.get_gemini_model()
            assert result == "gemini-1.0-pro"

    def test_get_gemini_model_with_default(self) -> None:
        """環境変数が設定されていない場合はデフォルト値を返す。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_gemini_model()
            assert result == "gemini-2.5-flash"

    def test_get_gemini_model_with_custom_default(self) -> None:
        """カスタムデフォルト値を指定できる。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_gemini_model(default="gemini-1.5-flash")
            assert result == "gemini-1.5-flash"
