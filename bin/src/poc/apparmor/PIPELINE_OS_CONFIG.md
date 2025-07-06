# OS設定によるパイプライン実現

## 概要

個々のflakeを変更するのではなく、**NixOSシステム全体**でAppArmorを強制する方法。

## 実装イメージ

### `/etc/nixos/configuration.nix`

```nix
{
  # AppArmor強制設定
  programs.apparmor-nix = {
    enable = true;
    
    # すべてのnix runに適用
    enforceByDefault = true;
    
    # プロファイルマッピング
    profiles = {
      # 特定のflakeに特定のプロファイル
      "github:nixos/nixpkgs" = "trusted";
      "github:some/untrusted-flake" = "strict";
      
      # デフォルトプロファイル
      default = "standard";
    };
    
    # 例外設定（root only）
    exceptions = [
      "github:trusted-org/*"
    ];
  };
  
  # nixコマンドのラッパー
  environment.shellAliases = {
    nix = "apparmor-nix";
  };
}
```

## 動作フロー

```
ユーザー: nix run github:some/flake
    ↓
OS設定: AppArmor必須チェック
    ↓
自動: プロファイル選択
    ↓
実行: aa-exec -p profile -- actual-command
```

## メリット

1. **透明性**: ユーザーは通常通りnixを使用
2. **強制力**: システムレベルで適用
3. **柔軟性**: プロファイルを中央管理
4. **既存flake変更不要**: そのまま使える

## 実装段階

### Phase 1: 現在（関数ラッパー）
- 手動でラップ
- 概念実証

### Phase 2: エイリアス/ラッパー
```bash
# /etc/nixos/configuration.nix
environment.systemPackages = [(
  pkgs.writeShellScriptBin "nix" ''
    if [[ "$1" == "run" ]]; then
      # AppArmorでラップして実行
      exec ${apparmor-nix}/bin/apparmor-nix "$@"
    else
      exec ${pkgs.nix}/bin/nix "$@"
    fi
  ''
)];
```

### Phase 3: Nixパッチ（理想）
- nix自体にAppArmorサポート追加
- upstreamへのPR

## 設定例

```nix
# ユーザーは普通にnixを使う
$ nix run github:some/tool

# システムが自動的に：
# 1. プロファイルを選択
# 2. AppArmorで実行
# 3. ログ記録
```

## セキュリティレベル

```nix
profiles = {
  # 完全信頼
  trusted = {
    network = true;
    home = "read-write";
  };
  
  # 標準
  standard = {
    network = true;
    home = "read-only";
    tmp = "read-write";
  };
  
  # 厳格
  strict = {
    network = false;
    home = "none";
    tmp = "read-write";
  };
};
```