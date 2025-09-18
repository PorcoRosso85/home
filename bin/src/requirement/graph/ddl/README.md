# DDL管理ディレクトリ

このディレクトリ（`/home/nixos/bin/src/requirement/graph/ddl/`）は、KuzuDB要件管理システムの**唯一の正式なDDL定義場所**です。

## 重要な原則

1. **単一ソースの原則**: すべてのスキーマ定義はこのディレクトリに配置
2. **他のDDLを参照禁止**: `/home/nixos/bin/src/kuzu/query/ddl/`等の他の場所のDDLは参照しない
3. **バージョン管理**: スキーマ変更はGitでバージョン管理（単一ファイル: schema.cypher）

## 現在のスキーマ

- `schema.cypher` - 現在の本番スキーマ（実装詳細プロパティを含む完全版）

## スキーマ適用方法

```bash
# apply_ddl_schema.pyを使用
cd /home/nixos/bin/src/requirement/graph/infrastructure
python apply_ddl_schema.py
```

## 開発ガイドライン

1. スキーマ変更は必ずTDDで実施
2. RED: 新しいプロパティ/テーブルが必要なテストを書く
3. GREEN: スキーマを更新してテストを通す
4. REFACTOR: スキーマの最適化

## 参照禁止リスト

以下のDDLファイルは参照しないこと：
- `/home/nixos/bin/src/kuzu/query/ddl/*`
- その他の場所にあるスキーマ定義

すべてのコードは`graph/ddl/`ディレクトリのスキーマのみを参照すること。