# /org モード共有DB設定ガイド

## 概要

複数のClaudeインスタンスが同じデータベースを共有して作業するための設定方法。

## 環境変数設定

### 通常モード（デフォルト）
```bash
export LD_LIBRARY_PATH="/path/to/gcc/lib"
export RGL_DB_PATH="/home/user/.rgl/default.db"
```

### /org モード（共有DB）
```bash
# 基本設定
export LD_LIBRARY_PATH="/path/to/gcc/lib"
export RGL_DB_PATH="/home/user/.rgl/default.db"

# /org モード有効化
export RGL_ORG_MODE="true"
export RGL_SHARED_DB_PATH="/home/user/.rgl/shared_org.db"
```

## 使用方法

1. 環境変数を設定
2. 各インスタンスが同じ`RGL_SHARED_DB_PATH`を参照
3. `RGL_ORG_MODE=true`の場合、自動的に共有DBを使用

## 注意事項

- 2回目以降の実行では`RGL_SKIP_SCHEMA_CHECK=true`を設定可能
- すべてのインスタンスで同じ環境変数を設定すること