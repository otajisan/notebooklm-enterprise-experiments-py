"""Gemini Proを使用したコンテンツ生成サービス。"""

import json
from datetime import datetime
from pathlib import Path

import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (
    get_service_account_key_info,
    get_service_account_key_path,
)


class ContentGenerator:
    """Gemini Proを使用してコンテンツを生成するサービス。

    検索結果（RAGの回答）を入力として、プレゼンテーション用の
    スライド構成をMarp互換のMarkdown形式で出力する。
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-2.5-flash",
        credentials: service_account.Credentials | None = None,
    ) -> None:
        """ContentGeneratorを初期化する。

        Args:
            project_id: GCPプロジェクトID
            location: GCPロケーション（例: "us-central1"）
            model_name: 使用するGeminiモデル名
            credentials: サービスアカウント認証情報（Noneの場合は環境変数から取得）
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        if credentials is None:
            credentials = self._load_credentials()

        # Vertex AI の初期化
        vertexai.init(
            project=project_id,
            location=location,
            credentials=credentials,
        )

        # Generative Model の初期化
        self.model = GenerativeModel(model_name)

    def _load_credentials(self) -> service_account.Credentials:
        """環境変数からサービスアカウント認証情報を読み込む。

        Returns:
            サービスアカウント認証情報

        Raises:
            ValueError: 認証情報が設定されていない場合
        """
        # まず、JSON文字列から読み込むことを試みる
        key_info = get_service_account_key_info()
        if key_info:
            return service_account.Credentials.from_service_account_info(key_info)

        # 次に、ファイルパスから読み込むことを試みる
        key_path = get_service_account_key_path()
        if key_path:
            key_path_obj = Path(key_path)
            if not key_path_obj.exists():
                raise ValueError(
                    f"サービスアカウントキーファイルが見つかりません: {key_path}"
                )
            return service_account.Credentials.from_service_account_file(
                str(key_path_obj)
            )

        raise ValueError(
            "サービスアカウント認証情報が設定されていません。"
            "GCP_SERVICE_ACCOUNT_KEY_PATHまたはGCP_SERVICE_ACCOUNT_KEY_JSONを"
            "設定してください。"
        )

    def generate_slide_markdown(self, source_text: str) -> str:  # noqa: E501
        """検索結果からスライド用のMarkdownを生成する。

        Args:
            source_text: RAGで取得した要約テキストや検索結果

        Returns:
            Marp互換のMarkdownテキスト
        """
        prompt = self._build_slide_prompt(source_text)
        response = self.model.generate_content(prompt)
        return response.text

    def _build_slide_prompt(self, source_text: str) -> str:
        """スライド生成用のプロンプトを構築する。

        Args:
            source_text: RAGで取得した要約テキストや検索結果

        Returns:
            プロンプト文字列
        """
        instructions = "\n".join(
            [
                "以下の情報を元に、プレゼンテーション用のスライド構成を作成してください。",
                "",
                "【出力要件】",
                "- Marpに対応したMarkdown形式で出力してください",
                "- 各スライドは `---` で区切ってください",
                "- 最初のスライドにはタイトルと概要を含めてください",
                "- 内容は箇条書きで整理してください",
                "- 最後のスライドにはまとめ・結論を含めてください",
                "- スライドは5〜8枚程度にまとめてください",
                "",
                "【入力情報】",
            ]
        )
        output_format = "\n".join(
            [
                "",
                "",
                "【出力形式】",
                "Markdownテキストのみを出力してください。説明や補足は不要です。",
                "最初の行は `---` から始め、Marpのフロントマターを含めてください。",
                "",
                "例:",
                "---",
                "marp: true",
                "theme: default",
                "paginate: true",
                "---",
                "",
                "# タイトル",
                "",
                "概要テキスト",
                "",
                "---",
                "",
                "## セクション1",
                "",
                "- ポイント1",
                "- ポイント2",
                "",
                "---",
            ]
        )
        return instructions + "\n" + source_text + output_format

    def generate_infographic_code(
        self, source_text: str, chart_type: str = "flowchart"
    ) -> str:
        """検索結果からMermaid.js図解コードを生成する。

        Args:
            source_text: RAGで取得した要約テキストや検索結果
            chart_type: 図の種類（flowchart, sequence, mindmap など）

        Returns:
            Mermaid.js記法のコード（Markdownコードブロック形式）
        """
        prompt = self._build_infographic_prompt(source_text, chart_type)
        response = self.model.generate_content(prompt)
        return response.text

    def _build_infographic_prompt(self, source_text: str, chart_type: str) -> str:
        """図解生成用のプロンプトを構築する。

        Args:
            source_text: RAGで取得した要約テキストや検索結果
            chart_type: 図の種類

        Returns:
            プロンプト文字列
        """
        chart_type_instructions = {
            "flowchart": "フローチャート（flowchart TD または flowchart LR）",
            "sequence": "シーケンス図（sequenceDiagram）",
            "mindmap": "マインドマップ（mindmap）",
            "classDiagram": "クラス図（classDiagram）",
            "stateDiagram": "状態遷移図（stateDiagram-v2）",
            "erDiagram": "ER図（erDiagram）",
            "gantt": "ガントチャート（gantt）",
        }
        chart_description = chart_type_instructions.get(chart_type, f"{chart_type}図")

        instructions = "\n".join(
            [
                f"以下のテキストの内容を説明する{chart_description}を作成してください。",
                "",
                "【出力要件】",
                "- 出力はMermaid.jsの構文のみにしてください",
                "- Markdownのコードブロック ```mermaid で囲んでください",
                "- ノードのラベルには日本語を使用してください",
                "- 図は見やすく構造化してください",
                "- 重要なポイントや関係性を明確に表現してください",
                "",
                "【入力情報】",
            ]
        )
        output_format = "\n".join(
            [
                "",
                "",
                "【出力形式】",
                "Mermaid.jsのコードブロックのみを出力してください。説明や補足は不要です。",
                "",
                "例:",
                "```mermaid",
                "flowchart TD",
                "    A[開始] --> B[処理1]",
                "    B --> C{条件分岐}",
                "    C -->|Yes| D[処理2]",
                "    C -->|No| E[処理3]",
                "    D --> F[終了]",
                "    E --> F",
                "```",
            ]
        )
        return instructions + "\n" + source_text + output_format

    def generate_answer_from_context(
        self, query: str, search_results: list[dict]
    ) -> str:
        """検索結果を元にユーザーの質問に対する回答を生成する。

        Args:
            query: ユーザーの質問
            search_results: 検索結果リスト（各要素は title, content, url を含む辞書）

        Returns:
            生成された回答テキスト
        """
        prompt = self._build_answer_prompt(query, search_results)
        response = self.model.generate_content(prompt)
        return response.text

    def _build_answer_prompt(self, query: str, search_results: list[dict]) -> str:
        """回答生成用のプロンプトを構築する。

        Args:
            query: ユーザーの質問
            search_results: 検索結果リスト

        Returns:
            プロンプト文字列
        """
        # コンテキストを構築
        context_parts: list[str] = []
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "無題")
            content = result.get("content", "")
            url = result.get("url", "")

            if content:
                context_parts.append(f"[Document {i}] {title}")
                context_parts.append(f"URL: {url}")
                context_parts.append(f"内容:\n{content}")
                context_parts.append("")

        context = "\n".join(context_parts)

        instructions = "\n".join(
            [
                "あなたは社内ドキュメントのアシスタントです。",
                "以下の検索結果（Context）のみに基づいて、質問（Question）に答えてください。",
                "",
                "【重要な指示】",
                "- 検索結果に含まれる情報のみを使用してください。",
                "- 日付指定がある場合は、その日付の情報を優先してください。",
                "- 回答は具体的かつ網羅的にしてください。",
                "- 情報が見つからない場合は、その旨を正直に伝えてください。",
                "- 回答の最後に、参照したドキュメントのタイトルとURLを記載。",
                "",
                "【Context】",
                context,
                "",
                "【Question】",
                query,
                "",
                "【Answer】",
            ]
        )
        return instructions

    def generate_search_params(self, user_query: str) -> dict:
        """自然言語の質問から検索パラメータを抽出する。

        Geminiを使用して、ユーザーの質問から検索キーワード、日付フィルタ、
        ソート順を構造化データとして抽出する。

        Args:
            user_query: ユーザーの質問

        Returns:
            検索パラメータを含む辞書:
            {
                "query": str,       # 検索キーワード
                "filter": str|None, # 日付フィルタ条件
                "order_by": str|None # ソート順
            }
        """
        prompt = self._build_search_params_prompt(user_query)
        response = self.model.generate_content(prompt)

        # レスポンスからJSONを抽出
        response_text = response.text.strip()

        # コードブロックを除去
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            params = json.loads(response_text)
            return {
                "query": params.get("query", user_query),
                "filter": params.get("filter"),
                "order_by": params.get("order_by"),
            }
        except json.JSONDecodeError:
            # JSONパースに失敗した場合はデフォルト値を返す
            return {
                "query": user_query,
                "filter": None,
                "order_by": None,
            }

    def _build_search_params_prompt(self, user_query: str) -> str:
        """検索パラメータ抽出用のプロンプトを構築する。

        Args:
            user_query: ユーザーの質問

        Returns:
            プロンプト文字列
        """
        # 現在の日時を取得
        current_date = datetime.now().strftime("%Y年%m月%d日")

        instructions = "\n".join(
            [
                f"現在の日時は {current_date} です。",
                "",
                "ユーザーの質問から、以下の情報を抽出してJSONで返してください：",
                "- query: 検索キーワード（時間表現を除いた検索文）",
                "- filter: 日付フィルタ条件（Vertex AI Search形式）",
                "- order_by: ソート順",
                "",
                "【ルール】",
                "1. 期間指定（例: 1/26〜1/30）の場合:",
                "   filter: \"date >= '2026-01-26' AND date <= '2026-01-30'\"",
                "",
                "2. 「直近」「最新」「最近」の場合:",
                '   order_by: "date desc"',
                "",
                "3. 「古い順」「日付順」の場合:",
                '   order_by: "date asc"',
                "",
                "4. 特定の日付（例: 1/30の）の場合:",
                "   filter: \"date = '2026-01-30'\"",
                "",
                "5. 日付指定がない場合:",
                "   filter: null, order_by: null",
                "",
                "6. 年が省略されている場合は現在の年を補完",
                "",
                "【出力形式】",
                "JSONのみを出力してください。説明は不要です。",
                "",
                "例1:",
                '入力: "2026/1/26〜1/30の議事録"',
                "出力:",
                "{",
                '  "query": "議事録",',
                "  \"filter\": \"date >= '2026-01-26' AND date <= '2026-01-30'\",",
                '  "order_by": null',
                "}",
                "",
                "例2:",
                '入力: "直近の朝会"',
                "出力:",
                "{",
                '  "query": "朝会",',
                '  "filter": null,',
                '  "order_by": "date desc"',
                "}",
                "",
                "例3:",
                '入力: "セキュリティに関するドキュメント"',
                "出力:",
                "{",
                '  "query": "セキュリティに関するドキュメント",',
                '  "filter": null,',
                '  "order_by": null',
                "}",
                "",
                "【ユーザーの質問】",
                user_query,
            ]
        )
        return instructions
