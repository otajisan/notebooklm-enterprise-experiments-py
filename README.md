# NotebookLM Enterprise Experiments Python

このプロジェクトは**ドメイン駆動設計（DDD: Domain-Driven Design）**の原則に基づいて構成されています。

## プロジェクト構造

```
notebooklm_enterprise_experiments_py/
├── domain/              # ドメインレイヤー
│   ├── entities/        # エンティティ（一意の識別子を持つドメインオブジェクト）
│   ├── value_objects/   # 値オブジェクト（識別子を持たない不変のドメインオブジェクト）
│   ├── repositories/    # リポジトリインターフェース（永続化の抽象化）
│   └── services/       # ドメインサービス（エンティティに属さないドメインロジック）
├── application/         # アプリケーションレイヤー
│   ├── services/        # アプリケーションサービス（ユースケースの実装）
│   └── dto/             # データ転送オブジェクト（レイヤー間のデータ転送）
├── infrastructure/      # インフラストラクチャレイヤー
│   ├── config/          # 設定管理（環境変数など）
│   ├── repositories/    # リポジトリ実装（ドメインリポジトリの具体的な実装）
│   └── external/        # 外部サービス連携（GCPなど）
└── interfaces/          # インターフェースレイヤー
    └── ...              # API、CLI、UIなどの外部との接点
```

### レイヤーの責務

- **Domain（ドメイン）**: ビジネスロジックとドメインモデル。他のレイヤーに依存しない。
- **Application（アプリケーション）**: ユースケースの実装。ドメインレイヤーに依存する。
- **Infrastructure（インフラストラクチャ）**: 技術的な実装（データベース、外部API、設定など）。ドメインとアプリケーションに依存する。
- **Interfaces（インターフェース）**: 外部との接点（API、CLI、UIなど）。他のすべてのレイヤーに依存する。

## セットアップ

### 環境変数の設定

シークレットな情報（GCPのプロジェクトIDなど）は環境変数で管理します。

1. `.env.example`をコピーして`.env`ファイルを作成してください：
   ```bash
   cp .env.example .env
   ```

2. `.env`ファイルを編集して、実際の値を設定してください：
   ```env
   GCP_PROJECT_ID=your-actual-project-id
   ```

3. `.env`ファイルは自動的に`.gitignore`に含まれているため、Gitにコミットされることはありません。

### 環境変数の使用方法

コード内で環境変数を使用する場合は、`notebooklm_enterprise_experiments_py.infrastructure.config`モジュールを使用してください：

```python
from notebooklm_enterprise_experiments_py.infrastructure.config import (
    get_gcp_project_id,
    get_gcp_region,
)

# GCPプロジェクトIDを取得
project_id = get_gcp_project_id()

# GCPリージョンを取得（デフォルト: us-central1）
region = get_gcp_region()
```

利用可能な関数：
- `get_gcp_project_id()`: GCPプロジェクトIDを取得（必須）
- `get_gcp_region(default="us-central1")`: GCPリージョンを取得
- `get_gcp_location(default="global")`: GCPロケーションを取得
- `get_env(key, default=None)`: 任意の環境変数を取得

## 開発ガイドライン

### DDDの原則に従った開発

1. **ドメインモデルを中心に設計する**: ビジネスロジックはドメインレイヤーに配置する
2. **依存関係の方向を守る**: ドメイン → アプリケーション → インフラストラクチャ → インターフェースの順に依存する
3. **リポジトリパターンを使用**: 永続化の詳細はインフラストラクチャレイヤーに隠蔽する
4. **値オブジェクトとエンティティを適切に使い分ける**: 識別子が必要な場合はエンティティ、不要な場合は値オブジェクト
