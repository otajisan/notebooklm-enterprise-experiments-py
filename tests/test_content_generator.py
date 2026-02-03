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
            patch.object(content_generator, "GenerativeModel") as mock_generative_model,
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
            patch.object(content_generator, "GenerativeModel") as mock_generative_model,
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

    def test_generate_infographic_code(self, generator: ContentGenerator) -> None:
        """generate_infographic_codeがMermaidコードを返す。"""
        mock_response = MagicMock()
        mock_response.text = """```mermaid
flowchart TD
    A[開始] --> B[処理1]
    B --> C{条件分岐}
    C -->|Yes| D[処理2]
    C -->|No| E[処理3]
    D --> F[終了]
    E --> F
```"""
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_infographic_code("テスト入力テキスト")

        assert "```mermaid" in result
        assert "flowchart" in result
        generator.model.generate_content.assert_called_once()

    def test_generate_infographic_code_with_chart_type(
        self, generator: ContentGenerator
    ) -> None:
        """chart_typeパラメータがプロンプトに含まれる。"""
        mock_response = MagicMock()
        mock_response.text = "```mermaid\nsequenceDiagram\n```"
        generator.model.generate_content.return_value = mock_response

        generator.generate_infographic_code("テスト入力", chart_type="sequence")

        # プロンプトにシーケンス図の指示が含まれていることを確認
        call_args = generator.model.generate_content.call_args
        prompt = call_args[0][0]
        assert "シーケンス図" in prompt

    def test_generate_infographic_code_with_source_text(
        self, generator: ContentGenerator
    ) -> None:
        """ソーステキストがプロンプトに含まれる。"""
        mock_response = MagicMock()
        mock_response.text = "```mermaid\nflowchart TD\n```"
        generator.model.generate_content.return_value = mock_response

        source_text = "稟議申請フローの説明テキスト"
        generator.generate_infographic_code(source_text)

        # プロンプトにソーステキストが含まれていることを確認
        call_args = generator.model.generate_content.call_args
        prompt = call_args[0][0]
        assert source_text in prompt

    def test_generate_search_params_with_date_range(
        self, generator: ContentGenerator
    ) -> None:
        """日付範囲指定がある場合、filterとorder_byを返す。"""
        mock_response = MagicMock()
        # JSONとして有効な形式（filter値内のダブルクォートはエスケープ）
        mock_response.text = (
            '{"query": "議事録", '
            '"filter": "date >= \\"2026-01-26\\" '
            'AND date <= \\"2026-01-30\\"", '
            '"order_by": null}'
        )
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_search_params("2026/1/26〜1/30の議事録")

        assert result["query"] == "議事録"
        assert "date >=" in result["filter"]
        assert result["order_by"] is None

    def test_generate_search_params_with_order_by(
        self, generator: ContentGenerator
    ) -> None:
        """「直近」の場合、order_byを返す。"""
        mock_response = MagicMock()
        mock_response.text = """{
            "query": "朝会",
            "filter": null,
            "order_by": "date desc"
        }"""
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_search_params("直近の朝会")

        assert result["query"] == "朝会"
        assert result["filter"] is None
        assert result["order_by"] == "date desc"

    def test_generate_search_params_without_date(
        self, generator: ContentGenerator
    ) -> None:
        """日付指定がない場合、filterとorder_byはNone。"""
        mock_response = MagicMock()
        mock_response.text = """{
            "query": "セキュリティに関するドキュメント",
            "filter": null,
            "order_by": null
        }"""
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_search_params("セキュリティに関するドキュメント")

        assert result["query"] == "セキュリティに関するドキュメント"
        assert result["filter"] is None
        assert result["order_by"] is None

    def test_generate_search_params_with_json_code_block(
        self, generator: ContentGenerator
    ) -> None:
        """JSONコードブロックが含まれていても正しくパースする。"""
        mock_response = MagicMock()
        mock_response.text = """```json
{
    "query": "議事録",
    "filter": "date = \\"2026-01-30\\"",
    "order_by": null
}
```"""
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_search_params("1/30の議事録")

        assert result["query"] == "議事録"
        assert result["filter"] == 'date = "2026-01-30"'

    def test_generate_search_params_invalid_json(
        self, generator: ContentGenerator
    ) -> None:
        """無効なJSONの場合、デフォルト値を返す。"""
        mock_response = MagicMock()
        mock_response.text = "invalid json"
        generator.model.generate_content.return_value = mock_response

        result = generator.generate_search_params("テストクエリ")

        assert result["query"] == "テストクエリ"
        assert result["filter"] is None
        assert result["order_by"] is None

    def test_generate_answer_from_context(self, generator: ContentGenerator) -> None:
        """検索結果から回答を生成する。"""
        mock_response = MagicMock()
        mock_response.text = "検索結果に基づく回答です。"
        generator.model.generate_content.return_value = mock_response

        search_results = [
            {
                "title": "ドキュメント1",
                "content": "テスト内容1",
                "url": "https://example.com/doc1",
            },
            {
                "title": "ドキュメント2",
                "content": "テスト内容2",
                "url": "https://example.com/doc2",
            },
        ]

        result = generator.generate_answer_from_context("質問文", search_results)

        assert result == "検索結果に基づく回答です。"

        # プロンプトに検索結果が含まれていることを確認
        call_args = generator.model.generate_content.call_args
        prompt = call_args[0][0]
        assert "ドキュメント1" in prompt
        assert "テスト内容1" in prompt
        assert "質問文" in prompt
