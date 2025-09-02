# Restricting Claude Code from Child Directories

## 調査結果サマリー

**結論**: Filesystem permissions (chmod 000) が最も効果的で簡単な解決策です。Firejailは権限エラーで動作しませんでした。

## 実証された解決策: Filesystem Permissions

### 成功したアプローチ
```bash
# 子ディレクトリのアクセス権を削除
chmod 000 test-dirs/child1 test-dirs/child2 test-dirs/child3
```

### テスト結果
✅ **完全にアクセスをブロック**:
- ファイル読み取り: Permission denied
- ディレクトリリスト: Permission denied
- ファイル書き込み: Permission denied
- サブディレクトリアクセス: Permission denied

### 実装ファイル
1. `filesystem-permissions-test.sh` - 権限制限の包括的テスト
2. `claude-with-restrictions.sh` - 自動権限管理ラッパー
3. `test-dirs/` - テスト用ディレクトリ構造

## Firejailの問題点

### エラー内容
```
Error ../../src/firejail/util.c:1041: create_empty_dir_as_root: mkdir: Permission denied
```

### 原因
- NixOSでfirejailはroot権限を要求
- サンドボックス作成に `/run/firejail` への書き込みが必要
- 非特権ユーザーでは動作不可

## 使用方法

### 簡単なテスト
```bash
# 権限を削除
chmod 000 test-dirs/child*

# アクセステスト（すべて失敗する）
cat test-dirs/child1/secret.txt  # Permission denied
ls test-dirs/child2/              # Permission denied
echo "test" > test-dirs/child3/newfile.txt  # Permission denied

# 権限を復元
chmod 755 test-dirs/child*
```

### ラッパースクリプトの使用
```bash
# 自動権限管理付きでシェル起動
./claude-with-restrictions.sh

# または直接Claude Codeを制限付きで起動
./claude-with-restrictions.sh env NIXPKGS_ALLOW_UNFREE=1 \
    nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure \
    -- --dangerously-skip-permissions
```

ラッパーの機能:
- 指定ディレクトリの権限を自動削除
- 終了時（Ctrl+C含む）に権限を自動復元
- 視覚的なフィードバック提供
- 任意のコマンドを制限付きで実行可能

## テスト実行方法

```bash
# テストディレクトリへ移動
cd /home/nixos/bin/src/poc/firejail-for-childs

# 権限ベースの制限テスト
./filesystem-permissions-test.sh

# ラッパースクリプトのテスト
./claude-with-restrictions.sh
```

## 結論

Claude Codeの子ディレクトリアクセス制限には:

1. **Filesystem permissions (chmod 000)** - 最も簡単で効果的
2. **ラッパースクリプト** - 自動化された権限管理
3. **将来的な改善** - Claude Codeに`.claudeignore`機能の追加を要望

この方法により、特別なツールや権限なしで確実なアクセス制限が実現できます。