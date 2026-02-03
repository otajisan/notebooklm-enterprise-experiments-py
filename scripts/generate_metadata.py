#!/usr/bin/env python3
"""GCSバケット内のドキュメントからメタデータファイル（JSONL）を生成するスクリプト。

このスクリプトは、GCSバケット内のドキュメントファイル（PDF, Word, Excel等）を
スキャンし、Vertex AI Search用のインポートメタデータファイル（JSONL形式）を生成する。

実行方法:
    # 環境変数のバケット名を使用
    python scripts/generate_metadata.py

    # バケット名を指定して実行
    python scripts/generate_metadata.py --bucket my-bucket-name

    # 出力ファイル名を指定
    python scripts/generate_metadata.py --output custom_metadata.jsonl

必要な環境変数:
    - GCP_PROJECT_ID: GCPプロジェクトID
    - GCS_BUCKET_NAME: GCSバケット名（--bucketオプションで上書き可能）
    - GCP_SERVICE_ACCOUNT_KEY_PATH または GCP_SERVICE_ACCOUNT_KEY_JSON: 認証情報
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import storage  # noqa: E402
from google.oauth2 import service_account  # noqa: E402

from notebooklm_enterprise_experiments_py.infrastructure.config.env_config import (  # noqa: E402
    get_gcp_project_id,
    get_gcs_bucket_name,
    get_service_account_key_info,
    get_service_account_key_path,
)

# サポートするファイル拡張子とMIME Typeのマッピング
_OOXML_BASE = "application/vnd.openxmlformats-officedocument"
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".docx": f"{_OOXML_BASE}.wordprocessingml.document",
    ".doc": "application/msword",
    ".xlsx": f"{_OOXML_BASE}.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".pptx": f"{_OOXML_BASE}.presentationml.presentation",
    ".ppt": "application/vnd.ms-powerpoint",
}


def get_mime_type(filename: str) -> str | None:
    """ファイル名から対応するMIME Typeを取得する。

    Args:
        filename: ファイル名

    Returns:
        MIME Type文字列、またはサポート外の場合はNone
    """
    ext = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext)


def is_supported_file(filename: str) -> bool:
    """ファイルがサポート対象かどうかを判定する。

    Args:
        filename: ファイル名

    Returns:
        サポート対象の場合True
    """
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def generate_document_id(blob_name: str) -> str:
    """blob名からVertex AI Search用の有効なドキュメントIDを生成する。

    Vertex AI Searchのid制約: [a-zA-Z0-9-_]* のみ許可
    日本語やスラッシュ、スペースを含むファイル名はSHA256ハッシュに変換する。

    Args:
        blob_name: GCSのblob名（例: "books/資料.pdf"）

    Returns:
        有効なドキュメントID（SHA256ハッシュの16進数文字列）
    """
    return hashlib.sha256(blob_name.encode("utf-8")).hexdigest()


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする。"""
    parser = argparse.ArgumentParser(
        description="GCSバケット内のドキュメントからメタデータファイル（JSONL）を生成する"
    )
    parser.add_argument(
        "--bucket",
        "-b",
        default=None,
        help="GCSバケット名（環境変数GCS_BUCKET_NAMEで設定可能）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="metadata.jsonl",
        help="出力ファイル名（デフォルト: metadata.jsonl）",
    )
    parser.add_argument(
        "--prefix",
        "-p",
        default="",
        help="スキャン対象のプレフィックス（フォルダパス）",
    )
    return parser.parse_args()


def load_credentials() -> service_account.Credentials:
    """サービスアカウント認証情報を読み込む。"""
    # まず、JSON文字列から読み込む
    key_info = get_service_account_key_info()
    if key_info:
        return service_account.Credentials.from_service_account_info(key_info)

    # 次に、ファイルパスから読み込む
    key_path = get_service_account_key_path()
    if key_path:
        key_path_obj = Path(key_path)
        if not key_path_obj.exists():
            raise ValueError(
                f"サービスアカウントキーファイルが見つかりません: {key_path}"
            )
        return service_account.Credentials.from_service_account_file(str(key_path_obj))

    raise ValueError(
        "サービスアカウント認証情報が設定されていません。"
        "GCP_SERVICE_ACCOUNT_KEY_PATHまたはGCP_SERVICE_ACCOUNT_KEY_JSONを設定。"
    )


def extract_date_from_filename(filename: str) -> str | None:
    """ファイル名から日付を抽出する。

    サポートするパターン:
    - YYYYMMDD (例: 20260130)
    - YYYY-MM-DD (例: 2026-01-30)
    - YYYY_MM_DD (例: 2026_01_30)

    Args:
        filename: ファイル名

    Returns:
        ISO 8601形式の日付文字列（YYYY-MM-DD）、または抽出できない場合はNone
    """
    # YYYYMMDD パターン
    match = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    if match:
        year, month, day = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # YYYY-MM-DD パターン
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if match:
        year, month, day = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # YYYY_MM_DD パターン
    match = re.search(r"(\d{4})_(\d{2})_(\d{2})", filename)
    if match:
        year, month, day = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def categorize_document(filename: str) -> str:
    """ファイル名からドキュメントカテゴリを推定する。

    Args:
        filename: ファイル名

    Returns:
        カテゴリ文字列
    """
    filename_lower = filename.lower()

    if any(kw in filename_lower for kw in ["議事録", "minutes", "mtg", "meeting"]):
        return "minutes"
    if any(kw in filename_lower for kw in ["報告", "report"]):
        return "report"
    if any(kw in filename_lower for kw in ["マニュアル", "manual", "guide"]):
        return "manual"
    if any(kw in filename_lower for kw in ["提案", "proposal"]):
        return "proposal"
    if any(kw in filename_lower for kw in ["朝会", "morning"]):
        return "morning_meeting"

    return "other"


def generate_metadata_entry(blob: storage.Blob, bucket_name: str) -> dict:
    """GCSのBlobオブジェクトからメタデータエントリを生成する。

    Args:
        blob: GCSのBlobオブジェクト
        bucket_name: バケット名

    Returns:
        メタデータエントリ（辞書）
    """
    filename = Path(blob.name).name

    # 日付を抽出（ファイル名から取れない場合はオブジェクトの更新日時を使用）
    date = extract_date_from_filename(filename)
    if not date and blob.updated:
        date = blob.updated.strftime("%Y-%m-%d")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # カテゴリを推定
    category = categorize_document(filename)

    # MIME Typeを決定（マッピングから取得、なければblobのcontent_typeを使用）
    mime_type = (
        get_mime_type(blob.name) or blob.content_type or "application/octet-stream"
    )

    # メタデータエントリを作成
    # idはVertex AI Searchの制約([a-zA-Z0-9-_]*)に準拠するためハッシュ化
    # 元のファイル名はstructData.filenameに保持
    entry = {
        "id": generate_document_id(blob.name),
        "structData": {
            "date": date,
            "category": category,
            "filename": blob.name,
        },
        "content": {
            "mimeType": mime_type,
            "uri": f"gs://{bucket_name}/{blob.name}",
        },
    }

    return entry


def main() -> None:
    """メイン関数。"""
    args = parse_args()

    print("=" * 60)
    print("GCS Metadata Generator")
    print("=" * 60)
    print()

    # 環境変数の取得
    try:
        project_id = get_gcp_project_id()
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)

    # バケット名の決定（コマンドライン引数 > 環境変数）
    bucket_name = args.bucket if args.bucket else get_gcs_bucket_name()
    if not bucket_name:
        print("エラー: GCSバケット名が指定されていません。")
        print("--bucket オプションまたは GCS_BUCKET_NAME 環境変数で指定してください。")
        sys.exit(1)

    print(f"プロジェクトID: {project_id}")
    print(f"バケット名: {bucket_name}")
    print(f"プレフィックス: {args.prefix or '(なし)'}")
    print(f"出力ファイル: {args.output}")
    print()

    # 認証情報の読み込み
    print("認証情報を読み込み中...")
    try:
        credentials = load_credentials()
        print("認証情報の読み込み完了")
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)

    # GCSクライアントの初期化
    print("GCSバケットをスキャン中...")
    try:
        storage_client = storage.Client(
            project=project_id,
            credentials=credentials,
        )
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=args.prefix))
    except Exception as e:
        print(f"GCSアクセスエラー: {e}")
        sys.exit(1)

    # サポート対象のファイルをフィルタリング
    supported_blobs = [b for b in blobs if is_supported_file(b.name)]

    # 拡張子ごとのファイル数を集計
    ext_counts: dict[str, int] = {}
    for blob in supported_blobs:
        ext = Path(blob.name).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    print(f"検出されたファイル: {len(supported_blobs)}件")
    for ext, count in sorted(ext_counts.items()):
        print(f"  - {ext}: {count}件")
    print()

    if not supported_blobs:
        print("警告: サポート対象のファイルが見つかりませんでした。")
        print(f"サポート対象: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        sys.exit(0)

    # メタデータエントリを生成
    print("メタデータを生成中...")
    entries = []
    for blob in supported_blobs:
        entry = generate_metadata_entry(blob, bucket_name)
        entries.append(entry)
        entry_date = entry["structData"]["date"]
        entry_type = entry["content"]["mimeType"]
        entry_filename = entry["structData"]["filename"]
        print(f"  - {entry_filename} (date: {entry_date}, type: {entry_type})")

    print()

    # JSONLファイルに出力
    output_path = Path(args.output)
    with output_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"出力完了: {output_path.absolute()}")
    print(f"生成されたエントリ数: {len(entries)}")
    print()

    print("=" * 60)
    print("次のステップ")
    print("=" * 60)
    print("1. 生成されたJSONLファイルをGCSバケットにアップロード")
    print("2. Vertex AI Agent Builder コンソールでデータをインポート")
    print("3. スキーマ設定で 'date' フィールドの [Filterable] と [Sortable] を有効化")
    print()


if __name__ == "__main__":
    main()
