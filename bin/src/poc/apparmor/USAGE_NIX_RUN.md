# nix runでのAppArmor使用方法

## 実現可能です！

### 通常実行（AppArmorなし）
```bash
$ nix run /path/to/flake#main
$ nix run nixpkgs#hello
$ nix run /home/nixos/bin/src/poc/readability
```

### AppArmor適用
```bash
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- /path/to/flake#main
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- nixpkgs#hello
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- /home/nixos/bin/src/poc/readability
```

## 具体例

### 1. readabilityをAppArmorで実行
```bash
# 通常
$ nix run /home/nixos/bin/src/poc/readability -- https://example.com

# AppArmor適用
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- /home/nixos/bin/src/poc/readability -- https://example.com
```

### 2. オプション付き
```bash
# 厳格プロファイル
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -p strict nixpkgs#hello

# Complainモード（テスト用）
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -c ./my-flake

# 詳細表示
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -v /home/nixos/bin/src/poc/similarity#ts
```

## エイリアス設定（便利）

```bash
# ~/.bashrc or ~/.zshrc
alias naa='nix run /home/nixos/bin/src/poc/apparmor#aa --'

# 使用
$ naa nixpkgs#hello
$ naa -p strict /home/nixos/bin/src/poc/tool
```

## メリット

1. **別途インストール不要** - nix runだけで完結
2. **明示的** - AppArmor適用が明確
3. **柔軟** - 必要なときだけ使用
4. **Unix的** - コマンドを組み合わせる哲学

## 動作原理

```
nix run /home/nixos/bin/src/poc/apparmor#aa
    ↓
aaスクリプトを実行
    ↓
引数のflakeをビルド
    ↓
aa-execでAppArmorプロファイル適用
    ↓
実際のプログラムを実行
```

## ヘルプ

```bash
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- --help
```