"""設定管理モジュールのテスト。"""

import json
import os
from pathlib import Path
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
        with patch.dict(
            os.environ, {"GCP_SERVICE_ACCOUNT_KEY_JSON": "invalid json"}
        ):
            with pytest.raises(ValueError, match="GCP_SERVICE_ACCOUNT_KEY_JSONの形式が不正です"):
                env_config.get_service_account_key_info()

    def test_get_service_account_key_info_without_env(self) -> None:
        """環境変数が設定されていない場合はNoneを返す。"""
        with patch.dict(os.environ, {}, clear=True):
            result = env_config.get_service_account_key_info()
            assert result is None
