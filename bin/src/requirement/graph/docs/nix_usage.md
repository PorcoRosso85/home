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

## 環境管理の仕組み

NixはC++ライブラリ（gcc）を提供し、uvがPythonパッケージ管理を担当します：

- **Nixの責務**: システムライブラリ（libstdc++など）の提供、LD_LIBRARY_PATHの設定
- **uvの責務**: Pythonパッケージ（kuzu含む）の管理、依存関係の解決

この分担により、Nix環境以外でも`LD_LIBRARY_PATH`を適切に設定すればuvで動作可能です。

## 利点

1. **環境の再現性**: どの環境でも同じ結果が得られる
2. **uvとの互換性**: Python開発者に馴染みのあるワークフロー
3. **自動的なライブラリ設定**: LD_LIBRARY_PATHが自動的に設定される
4. **クリーンな分離**: システムライブラリとPythonパッケージの責務が明確

## トラブルシューティング

### flake.nixが見つからない場合
```bash
git add flake.nix
```

### ロックファイルの更新
```bash
nix flake update
```