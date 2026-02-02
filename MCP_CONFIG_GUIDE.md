# MCP Server Configuration Guide

このガイドでは、RAG MCPサーバーをCursorやClaude Desktopなどのクライアントに設定する方法を説明します。

## 前提条件

1. **Python環境**: Python 3.13以上がインストールされていること
2. **uv**: Pythonパッケージマネージャーがインストールされていること
3. **GCP認証情報**: サービスアカウントキーが設定されていること
4. **環境変数**: `.env`ファイルに必要な環境変数が設定されていること

### 必要な環境変数

`.env`ファイルに以下を設定してください:

```bash
GCP_PROJECT_ID=your-project-id
ENGINE_ID=your-search-engine-id
LOCATION=global
GEMINI_MODEL=gemini-2.5-flash  # オプション
GCP_SERVICE_ACCOUNT_KEY_PATH=/path/to/service-account-key.json
# または
GCP_SERVICE_ACCOUNT_KEY_JSON='{"type": "service_account", ...}'
```

## Cursorでの設定

### 設定方法

1. Cursorを開き、`Settings` > `Features` > `MCP` に移動
2. 「Add New MCP Server」をクリック
3. 以下の設定を追加:

### 設定JSON

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/notebooklm-enterprise-experiments-py",
        "python",
        "servers/rag_server.py"
      ],
      "env": {
        "GCP_PROJECT_ID": "your-project-id",
        "ENGINE_ID": "your-search-engine-id",
        "LOCATION": "global",
        "GCP_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account-key.json"
      }
    }
  }
}
```

> **注意**: `/path/to/notebooklm-enterprise-experiments-py`をプロジェクトの実際のパスに置き換えてください。

## Claude Desktopでの設定

### 設定ファイルの場所

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 設定JSON

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/notebooklm-enterprise-experiments-py",
        "python",
        "servers/rag_server.py"
      ],
      "env": {
        "GCP_PROJECT_ID": "your-project-id",
        "ENGINE_ID": "your-search-engine-id",
        "LOCATION": "global",
        "GCP_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account-key.json"
      }
    }
  }
}
```

## 利用可能なツール

このMCPサーバーは以下の3つのツールを提供します:

### 1. `search_documents`

社内ドキュメント（PDF/Googleドライブ）を検索し、要約と引用元を返します。

**引数:**
- `query` (string, 必須): 検索キーワードや質問内容

**使用例:**
```
「リモートワークに関する社内規定を検索して」
```

### 2. `generate_slide_draft`

指定されたトピックや検索結果に基づき、スライド構成案（Markdown）を生成します。

**引数:**
- `query` (string, 必須): スライドのテーマ

**使用例:**
```
「DDDの基本についてのスライドを作成して」
```

### 3. `generate_diagram`

指定されたトピックに基づき、図解（フローチャート等）のMermaidコードを生成します。

**引数:**
- `query` (string, 必須): 図解したい内容
- `chart_type` (string, オプション): 図の種類（デフォルト: "flowchart"）
  - `flowchart`: フローチャート
  - `sequence`: シーケンス図
  - `mindmap`: マインドマップ
  - `classDiagram`: クラス図
  - `stateDiagram`: 状態遷移図
  - `erDiagram`: ER図
  - `gantt`: ガントチャート

**使用例:**
```
「稟議申請フローをフローチャートにして」
「APIの呼び出しフローをシーケンス図にして」
```

## 使用例

### 会話例1: ドキュメント検索

```
ユーザー: @rag-server 社内規定の"リモートワーク"に関する記述を検索して
AI: (search_documentsツールを呼び出し、検索結果を表示)
```

### 会話例2: スライド生成

```
ユーザー: @rag-server セキュリティ研修用のスライドを作成して
AI: (generate_slide_draftツールを呼び出し、Marp形式のMarkdownを生成)
```

### 会話例3: 図解生成

```
ユーザー: @rag-server 今の内容をわかりやすくフローチャートにして
AI: (generate_diagramツールを呼び出し、Mermaid図を生成)
```

## トラブルシューティング

### サーバーが起動しない場合

1. **依存関係の確認**:
   ```bash
   uv sync
   ```

2. **環境変数の確認**:
   ```bash
   uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GCP_PROJECT_ID'))"
   ```

3. **サーバーの直接起動テスト**:
   ```bash
   uv run python servers/rag_server.py
   ```
   エラーなく待機状態になれば正常です（Ctrl+Cで終了）。

### 認証エラーの場合

1. サービスアカウントキーのパスが正しいか確認
2. サービスアカウントに必要な権限があるか確認:
   - Discovery Engine API User
   - Vertex AI User

### ツールが表示されない場合

1. クライアントを再起動
2. 設定JSONの構文エラーを確認
3. `command`と`args`のパスが正しいか確認
