# コマンドごとにAppArmorを無効化する方法

## 1. 環境変数による制御

```bash
# 環境変数でAppArmorを無効化
$ DISABLE_APPARMOR=1 nix run /home/nixos/bin/src/poc/apparmor#aa -- nixpkgs#hello

# または
$ NO_APPARMOR=1 aa nixpkgs#hello
```

## 2. フラグによる無効化

```bash
# --no-apparmorフラグ
$ aa --no-apparmor nixpkgs#hello

# または短縮形
$ aa -n nixpkgs#hello
```

## 3. unconfined プロファイルの使用

```bash
# unconfinedプロファイルを明示的に指定
$ aa -p unconfined nixpkgs#hello
```

## 実装例

### 環境変数チェックの追加

```nix
# aaコマンドに追加
if [[ -n "$DISABLE_APPARMOR" ]] || [[ -n "$NO_APPARMOR" ]]; then
  echo "⚠️  AppArmor disabled by environment variable"
  exec "$exe" "$@"
fi
```

### フラグオプションの追加

```nix
case "$1" in
  -n|--no-apparmor)
    no_apparmor=1
    shift
    ;;
esac

# 実行時
if [[ $no_apparmor -eq 1 ]]; then
  echo "⚠️  AppArmor disabled by flag"
  exec "$exe" "$@"
fi
```

## 使用例

### 開発時のデバッグ

```bash
# 通常実行（AppArmorあり）
$ aa ./my-app

# 問題があった場合、AppArmorなしで確認
$ aa --no-apparmor ./my-app

# または
$ DISABLE_APPARMOR=1 aa ./my-app
```

### CI/CDでの使用

```yaml
# GitHub Actions例
- name: Run with AppArmor
  run: aa ./my-app
  
- name: Run without AppArmor (fallback)
  run: aa --no-apparmor ./my-app
  if: failure()
```

### スクリプトでの条件分岐

```bash
#!/bin/bash

# 開発環境ではAppArmorを無効化
if [[ "$ENVIRONMENT" == "development" ]]; then
  export DISABLE_APPARMOR=1
fi

# 実行
aa ./my-app
```

## セキュリティ考慮事項

1. **本番環境では使用しない**
   - デバッグ・開発時のみ使用
   - 本番環境では常にAppArmorを有効に

2. **ログに記録**
   - AppArmorが無効化された場合は必ずログに記録
   - 監査証跡として重要

3. **権限制御**
   - 無効化オプションの使用を特定ユーザーに制限
   - sudoersで制御することも可能