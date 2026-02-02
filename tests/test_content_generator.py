"""ContentGeneratorのテスト。"""

from unittest.mock import MagicMock, patch

import pytest

from notebooklm_enterprise_experiments_py.infrastructure.external import (
    content_generator,
)

ContentGenerator = content_generator.ContentGenerator


class TestContentGenerator:
    """ContentGeneratorのテスト。"""

    @pytest.fixture
    def mock_credentials(self) -> MagicMock:
        """モックの認証情報を作成する。"""
        return MagicMock()

    @pytest.fixture
    def generator(self, mock_credentials: MagicMock) -> ContentGenerator:
        """テスト用のジェネレータインスタンスを作成する。"""
        with (
            patch.object(content_generator, "vertexai") as mock_vertexai,
            patch.object(
                content_generator, "GenerativeModel"
            ) as mock_generative_model,
        ):
            mock_vertexai.init = MagicMock()
            mock_generative_model.return_value = MagicMock()
            return ContentGenerator(
                project_id="test-project",
                location="us-central1",
                model_name="gemini-1.5-pro",
                credentials=mock_credentials,
            )

    def test_init_with_credentials(self, mock_credentials: MagicMock) -> None:
        """認証情報を指定して初期化できる。"""
        with (
            patch.object(content_generator, "vertexai") as mock_vertexai,
            patch.object(
                content_generator, "GenerativeModel"
            ) as mock_generative_model,
        ):
            generator = ContentGenerator(
                project_id="test-project",
                location="us-central1",
                model_name="gemini-1.5-pro",
                credentials=mock_credentials,
            )
            assert generator.project_id == "test-project"
            assert generator.location == "us-central1"
            assert generator.model_name == "gemini-1.5-pro"
            mock_vertexai.init.assert_called_once_with(
                project="test-project",
                location="us-central1",
                credentials=mock_credentials,
            )
            mock_generative_model.assert_called_once_with("gemini-1.5-pro")

    def test_generate_slide_markdown(self, generator: ContentGenerator) -> None:
        """generate_slide_markdownがMarkdownを返す。"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.text = """---
marp: true
theme: default
---

# テストスライド

テスト内容

---

## まとめ

- ポイント1
"""
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_slide_markdown("テスト入力テキスト")

        assert "marp: true" in result
        assert "# テストスライド" in result
        assert "---" in result
        generator.model.generate_content.assert_called_once()

    def test_generate_slide_markdown_with_source_text(
        self, generator: ContentGenerator
    ) -> None:
        """ソーステキストがプロンプトに含まれる。"""
        mock_response = MagicMock()
        mock_response.text = "# Slide"
        generator.model.generate_content.return_value = mock_response

        source_text = "セキュリティ研修の要約テキスト"
        generator.generate_slide_markdown(source_text)

        # プロンプトにソーステキストが含まれていることを確認
        call_args = generator.model.generate_content.call_args
        prompt = call_args[0][0]
        assert source_text in prompt

    def test_load_credentials_without_env(self) -> None:
        """認証情報が設定されていない場合はエラーを発生させる。"""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(
                content_generator,
                "get_service_account_key_info",
                return_value=None,
            ),
            patch.object(
                content_generator,
                "get_service_account_key_path",
                return_value=None,
            ),
        ):
            with pytest.raises(
                ValueError, match="サービスアカウント認証情報が設定されていません"
            ):
                ContentGenerator(
                    project_id="test-project",
                    location="us-central1",
                )
