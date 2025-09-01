# README Graph

## 目的
プロジェクト内のmodule.jsonファイルを検証・インデックス化し、モジュール間の依存関係を可視化するツール

## これは何か
- module.jsonファイルの検証・クエリツール
- プロジェクト構造の整合性チェッカー
- 依存関係グラフのビルダー

## これは何でないか
- READMEの代替システムではない
- メタフレームワークではない
- 単なるツールである

## 使い方

### 1. module.jsonをプロジェクトに配置
各ディレクトリに`module.json`を配置:
```json
{
  "id": "your-module",
  "path": "/path/to/module",
  "purpose": "What this module does",
  "type": "service|library|tool|infrastructure",
  "dependencies": ["other-module-id"],
  "interfaces": {...},
  "responsibilities": [...],
  "constraints": {...}
}
```

### 2. ツールを実行

```bash
# module.jsonファイルを探索
python crawler.py /path/to/project

# 検証（実装予定）
python validator.py /path/to/project

# グラフ構築（実装予定）
python indexer.py /path/to/project

# クエリ（実装予定）
python query.py "MATCH (m:Module) RETURN m"
```

## コンポーネント

| ファイル | 責務 |
|---------|------|
| crawler.py | module.jsonファイルを探索 |
| validator.py | スキーマに対して検証 |
| indexer.py | KuzuDBにグラフ構築 |
| query.py | グラフのクエリ実行 |

## 技術スタック
- Python: シンプルなスクリプト群
- KuzuDB: グラフデータベース
- JSON: モジュール定義フォーマット