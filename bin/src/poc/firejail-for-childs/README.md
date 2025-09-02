# Restricting Claude Code from Child Directories

## 調査結果サマリー

**結論**: 2つの有効な制限方法が実証されています。

1. **Filesystem permissions (chmod 000)** - 最も簡単で確実
2. **Firejail with nix develop** - サンドボックス環境での制限

## 実証された解決策

### 方法1: Filesystem Permissions
```bash
# 子ディレクトリのアクセス権を削除
chmod 000 test-dirs/child1 test-dirs/child2 test-dirs/child3
```

**テスト結果** ✅:
- ファイル読み取り: Permission denied
- ディレクトリリスト: Permission denied
- ファイル書き込み: Permission denied
- サブディレクトリアクセス: Permission denied

### 方法2: Firejail with nix develop
```bash
# 正しい使用方法（実証済み）
nix develop -c firejail --noprofile --blacklist=$PWD/test-dirs/child1 -- command
```

**重要**: `nix develop -c firejail` の順序が必要（`firejail nix run`は失敗）

## Firejailの使用方法

### ✅ 成功する方法
```bash
# Claude Code用
nix develop -c firejail \
    --noprofile \
    --blacklist=$PWD/restricted-directories \
    --read-only=/nix/store \
    -- env NIXPKGS_ALLOW_UNFREE=1 \
       nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure \
       -- --dangerously-skip-permissions
```

### ❌ 失敗する方法
```bash
# これは動作しない
firejail nix run .#claude
```

**理由**: Nixデーモンがサンドボックス外でプロセスを起動するため

## 実装ファイル
1. `filesystem-permissions-test.sh` - 権限制限の包括的テスト
2. `claude-with-restrictions.sh` - 自動権限管理ラッパー
3. `test-simple.sh` - KISS原則に基づく簡易テスト
4. `test-dirs/` - テスト用ディレクトリ構造

## 使用例

### 方法1: Filesystem Permissions
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

### 方法2: Firejail（実証済み）
```bash
# シンプルなテスト
nix develop -c firejail --noprofile --blacklist=$PWD/test-dirs/child1 \
    -- ls test-dirs/child1
# 結果: Permission denied ✅
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

## テスト実行方法

```bash
# テストディレクトリへ移動
cd /home/nixos/bin/src/poc/firejail-for-childs

# 権限ベースの制限テスト
./filesystem-permissions-test.sh

# Firejailの簡易テスト
./test-simple.sh

# ラッパースクリプトのテスト
./claude-with-restrictions.sh
```

## 推奨事項

### シンプルな用途
1. **chmod 000** - 最も簡単で確実、権限復元が容易

### セキュアな環境
2. **nix develop -c firejail** - サンドボックス環境、より細かい制御が可能

### 自動化が必要な場合
3. **ラッパースクリプト** - 権限管理の自動化、視覚的フィードバック

## 結論

Claude Codeの子ディレクトリアクセス制限には実証済みの複数の方法があります。
用途に応じて最適な方法を選択し、確実なアクセス制限を実現できます。