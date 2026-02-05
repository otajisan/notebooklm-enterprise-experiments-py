"""サンプルテストファイル。"""

import os
from unittest.mock import patch

from notebooklm_enterprise_experiments_py import __version__
from notebooklm_enterprise_experiments_py.config import env_config


def test_version():
    """パッケージのバージョンをテストする。"""
    assert __version__ == "0.1.0"


def test_get_env_with_existing_key():
    """存在する環境変数を取得するテスト。"""
    with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
        result = env_config.get_env("TEST_KEY")
        assert result == "test_value"


def test_get_env_with_missing_key():
    """存在しない環境変数を取得するテスト（デフォルト値なし）。"""
    with patch.dict(os.environ, {}, clear=True):
        result = env_config.get_env("NON_EXISTENT_KEY")
        assert result is None


def test_get_env_with_default():
    """存在しない環境変数を取得するテスト（デフォルト値あり）。"""
    with patch.dict(os.environ, {}, clear=True):
        result = env_config.get_env("NON_EXISTENT_KEY", default="default_value")
        assert result == "default_value"


def test_get_gcp_region_with_default():
    """GCPリージョンを取得するテスト（デフォルト値使用）。"""
    with patch.dict(os.environ, {}, clear=True):
        result = env_config.get_gcp_region()
        assert result == "us-central1"


def test_get_gcp_region_with_env():
    """GCPリージョンを取得するテスト（環境変数から取得）。"""
    with patch.dict(os.environ, {"GCP_REGION": "asia-northeast1"}):
        result = env_config.get_gcp_region()
        assert result == "asia-northeast1"


def test_get_gcp_location_with_default():
    """GCPロケーションを取得するテスト（デフォルト値使用）。"""
    with patch.dict(os.environ, {}, clear=True):
        result = env_config.get_gcp_location()
        assert result == "global"


def test_get_gcp_location_with_env():
    """GCPロケーションを取得するテスト（環境変数から取得）。"""
    with patch.dict(os.environ, {"GCP_LOCATION": "us-central1"}, clear=True):
        result = env_config.get_gcp_location()
        assert result == "us-central1"
