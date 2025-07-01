# Nix を使った実行方法

## 概要

RGLはNixを使って環境を管理し、依存関係を解決します。これにより、環境変数やライブラリパスの設定が自動化されます。

## 基本的な使い方

### 開発環境の起動
```bash
nix develop
# または
nix-shell
```

### テストの実行
```bash
# すべてのテストを実行
nix run .#test

# 特定のテストファイルを実行
nix run .#test -- infrastructure/test_variables.py

# 特定のテストケースを実行
nix run .#test -- infrastructure/test_kuzu_repository.py::TestKuzuRepository::test_kuzu_repository_basic_crud_returns_saved_requirement -v
```

### メインアプリケーションの実行
```bash
# RGLを実行
nix run

# Cypherクエリを実行
echo 'MATCH (n:RequirementEntity) RETURN n LIMIT 5' | nix run
```

### スキーマ適用
```bash
nix run .#apply-schema
```

## 移行ガイド

以前は`test.sh`を使用していましたが、現在はNixで環境を完全に管理しています：

```bash
# 以前
./test.sh

# 現在
nix run .#test
```

## 利点

1. **環境の再現性**: どの環境でも同じ結果が得られる
2. **自動的な依存解決**: gcc、Python、uvなどが自動的に設定される
3. **環境変数の管理**: LD_LIBRARY_PATHなどが自動的に設定される
4. **クリーンな環境**: システムのPythonパッケージと混在しない

## トラブルシューティング

### flake.nixが見つからない場合
```bash
git add flake.nix
```

### ロックファイルの更新
```bash
nix flake update
```