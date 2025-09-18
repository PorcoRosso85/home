# ローカルFlakeでのaa使用例

## 基本的な使い方

```bash
# bin/src/poc配下のflakeを実行
$ aa /home/nixos/bin/src/poc/readability
$ aa /home/nixos/bin/src/poc/similarity#ts
$ aa /home/nixos/bin/src/poc/xxx/flake#main

# 相対パスも可能
$ cd /home/nixos/bin/src/poc
$ aa ./readability
$ aa ./similarity#ts --help

# プロファイル指定
$ aa -p strict /home/nixos/bin/src/poc/untrusted-tool
$ aa -c ./new-tool  # complainモードでテスト
```

## 実行例

### readabilityの場合
```bash
# 通常実行
$ nix run /home/nixos/bin/src/poc/readability -- --help

# AppArmor適用
$ aa /home/nixos/bin/src/poc/readability -- --help
$ aa -v /home/nixos/bin/src/poc/readability -- https://example.com -o output.md
```

### similarityの場合
```bash
# 通常実行
$ nix run /home/nixos/bin/src/poc/similarity#ts

# AppArmor適用（読み取り専用で安全）
$ aa /home/nixos/bin/src/poc/similarity#ts ./src
$ aa -p strict /home/nixos/bin/src/poc/similarity#ts  # ネットワークも禁止
```

## エイリアス設定（便利）

```bash
# ~/.bashrc or ~/.zshrc
alias aa-read='aa /home/nixos/bin/src/poc/readability --'
alias aa-sim='aa /home/nixos/bin/src/poc/similarity#ts'

# 使用
$ aa-read https://example.com
$ aa-sim ./my-code
```

## 開発時のワークフロー

```bash
# 1. 新しいツールを開発
$ cd /home/nixos/bin/src/poc/my-new-tool
$ nix develop

# 2. 通常テスト
$ nix run . -- test-args

# 3. AppArmorでテスト（complainモード）
$ aa -c . -- test-args
🔒 Applying AppArmor profile 'restricted' in complain mode
⚠️  Violations will be logged but not blocked

# 4. 厳格モードでテスト
$ aa -p strict . -- test-args
```

## プロファイルごとの制限

### restricted（デフォルト）
- ✅ ネットワークアクセス
- ✅ /tmp書き込み
- ✅ ホーム読み取り
- ❌ ~/.ssh, ~/.gnupg アクセス

### strict
- ❌ ネットワークアクセス  
- ✅ /tmp書き込み
- ❌ ホームディレクトリアクセス
- ✅ Nix store読み取り

## トラブルシューティング

```bash
# 詳細モードで何が起きているか確認
$ aa -v /home/nixos/bin/src/poc/tool
🔒 Applying AppArmor profile 'restricted' in enforce mode
📦 Built: /nix/store/xxx-tool-1.0.0
🚀 Executing: /nix/store/xxx-tool-1.0.0/bin/tool

# AppArmorが使えない環境
$ aa /home/nixos/bin/src/poc/tool
Warning: AppArmor not available, running without protection
[通常実行される]
```