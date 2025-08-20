# PR TIMES 人物名抽出ツール

## 概要
PR TIMES記事から人物名を自動抽出するツール。`../corporate_list`で収集したPR TIMES記事データを解析し、記事内に登場する人物名を抽出します。

## 機能
- PR TIMES記事HTMLからの人物名抽出
- 日本語の人名パターン認識
- 役職付き人名の検出（例：「代表取締役 山田太郎」）
- 抽出結果のJSON/CSV出力

## 使用方法
```bash
# 開発環境に入る
nix develop

# 単一記事から人物名を抽出
nix run . -- extract --file ../corporate_list/data/article.html

# ディレクトリ内の全記事を処理
nix run . -- extract --dir ../corporate_list/data/

# 結果をJSONで出力
nix run . -- extract --dir ../corporate_list/data/ --output persons.json
```

## 出力形式
```json
{
  "article_url": "https://prtimes.jp/...",
  "extracted_at": "2024-08-21T00:00:00Z",
  "persons": [
    {
      "name": "山田太郎",
      "title": "代表取締役",
      "context": "代表取締役の山田太郎は..."
    }
  ]
}
```

## 技術スタック
- Python 3.11+
- BeautifulSoup4 (HTML解析)
- spaCy/GiNZA (日本語NLP)
- Nix (開発環境管理)

## 開発
```bash
# テスト実行
nix develop -c pytest

# 型チェック
nix develop -c mypy src/

# リンター
nix develop -c ruff check src/
```

## ディレクトリ構造
```
.
├── flake.nix           # Nix設定
├── README.md           # このファイル
├── src/
│   ├── __init__.py
│   ├── extractor.py    # 人物名抽出ロジック
│   └── cli.py          # CLIインターフェース
└── tests/
    └── test_extractor.py
```