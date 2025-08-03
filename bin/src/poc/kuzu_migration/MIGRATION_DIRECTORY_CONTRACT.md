# KuzuDB Migration ディレクトリ構成契約

## 概要
このドキュメントは、kuzu-migrateツールが管理するddlディレクトリ構成の契約を定義します。

## ディレクトリ構成

### プロジェクト側
```
<project-root>/
├── ddl/                          # [必須] DDLディレクトリ（プロジェクトが作成）
│   ├── migrations/              # [kuzu-migrate管理] マイグレーション
│   │   ├── 000_initial.cypher  # [kuzu-migrate管理] 初期スキーマ
│   │   └── NNN_description.cypher
│   └── snapshots/              # [kuzu-migrate管理] スナップショット
│       └── v1.0.0/
└── data/
    └── kuzu.db                  # [慣例] データベースファイル
```

## 契約詳細

### 1. ddl/ ディレクトリ
- **責任**: プロジェクト側が作成
- **要求**: プロジェクトルートに`ddl/`ディレクトリが存在すること
- **不在時**: エラーで即座に終了

### 2. migrations/ および snapshots/ ディレクトリ
- **責任**: kuzu-migrateが完全管理
- **作成**: kuzu-migrate initまたは初回実行時に自動作成
- **手動編集**: 推奨しない（ツール経由でのみ変更）

### 3. 000_initial.cypher
- **管理**: kuzu-migrateが生成・管理
- **内容**: `EXPORT DATABASE --schema-only`の出力
- **目的**: 新規環境構築時の起点
- **更新**: kuzu-migrate snapshot実行時に自動更新

### 4. マイグレーションファイル命名規則
- **形式**: `NNN_description.cypher`
- **番号**: 3桁のゼロパディング（001, 002, ... 999）
- **説明**: snake_case、動詞で開始（add_、create_、remove_）
- **例**: 
  - `001_create_user_table.cypher`
  - `002_add_email_to_users.cypher`
  - `003_remove_deprecated_fields.cypher`

## ツールの呼び出し方

### CLI引数
```bash
# ddlディレクトリを指定
kuzu-migrate --ddl ./ddl apply
kuzu-migrate --ddl ./ddl snapshot

# デフォルトはddl/
kuzu-migrate apply
```

### 環境変数
- `KUZU_DDL_DIR`: DDLディレクトリ（デフォルト: ./ddl）
- `KUZU_DB_PATH`: データベースパス（デフォルト: ./data/kuzu.db）

## Nix Flake統合

### kuzu-migrateのflake.nix
```nix
lib.mkKuzuMigration = { ddlPath ? "./ddl" }: {
  apps = {
    migrate = {
      type = "app";
      program = "${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} apply";
    };
    snapshot = {
      type = "app";
      program = "${kuzu-migrate}/bin/kuzu-migrate --ddl ${ddlPath} snapshot";
    };
  };
};
```

### プロジェクト側のflake.nix
```nix
inputs.kuzu-migrate.url = "github:org/kuzu-migrate";

outputs = { self, kuzu-migrate, ... }: {
  apps = kuzu-migrate.lib.mkKuzuMigration { 
    ddlPath = "./ddl";  # プロジェクトのddlディレクトリ
  };
};
```

## 契約違反時の動作

1. **ddl/不在**: 
   ```
   ❌ ERROR: ddl/ directory not found
   Please create it: mkdir ddl
   ```
   
2. **migrations/不在**: kuzu-migrateが自動作成

3. **000_initial.cypher不在**: 
   ```
   ❌ No initial schema found
   Run: kuzu-migrate init
   ```

## 責任分界

### プロジェクト側の責任
- ddl/ディレクトリの作成
- データベースファイルの管理

### kuzu-migrateの責任
- ddl/migrations/の管理
- ddl/snapshots/の管理  
- マイグレーションの実行と追跡

この明確な分離により、プロジェクト構造の自由度を保ちつつ、DDL管理の一貫性を確保します。

作成日: 2025-08-03
契約バージョン: 1.0