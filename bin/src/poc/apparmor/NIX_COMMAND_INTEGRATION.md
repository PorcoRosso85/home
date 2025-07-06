# nixコマンドでのAppArmor統合方法

## 方法1: nixコマンドのエイリアス/ラッパー

```bash
# ~/.bashrc or ~/.zshrc
nix() {
  if [[ "$1" == "run" ]] && [[ "${2}" == "--aa" ]]; then
    # --aa フラグを検出
    shift 2  # "run --aa" を削除
    aa "$@"  # aaコマンドに委譲
  else
    # 通常のnixコマンド
    command nix "$@"
  fi
}

# 使用例
$ nix run --aa nixpkgs#hello
$ nix run --aa /home/nixos/bin/src/poc/readability
$ nix run nixpkgs#hello  # 通常実行（AppArmorなし）
```

## 方法2: nix runのカスタムフラグ（環境変数）

```bash
# ~/.bashrc
nix-run() {
  if [[ -n "$NIX_APPARMOR" ]]; then
    aa "$@"
  else
    nix run "$@"
  fi
}

# 使用例
$ NIX_APPARMOR=1 nix-run nixpkgs#hello
$ NIX_APPARMOR=strict nix-run /home/nixos/bin/src/poc/tool
```

## 方法3: nixのプラグインシステム（将来的）

```nix
# /etc/nixos/configuration.nix
{
  nix.extraOptions = ''
    plugin-files = ${pkgs.nix-apparmor-plugin}/lib/nix/plugins/apparmor.so
  '';
  
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" "plugins" ];
    
    # AppArmorプラグイン設定
    apparmor-integration = {
      enable = true;
      default-profile = "restricted";
      
      # 特定のパターンに自動適用
      auto-apply = [
        "github:untrusted/*"
        "/home/*/downloads/*"
      ];
    };
  };
}

# 使用（自動的にAppArmor適用）
$ nix run github:untrusted/tool  # 自動でAppArmor適用
$ nix run --no-apparmor github:untrusted/tool  # 明示的に無効化
```

## 方法4: nix run のラッパースクリプト

```nix
# flake.nix
{
  packages.nix-aa = pkgs.writeShellScriptBin "nix" ''
    # 本物のnixコマンドのパス
    real_nix="${pkgs.nix}/bin/nix"
    
    # runサブコマンドをインターセプト
    if [[ "$1" == "run" ]]; then
      shift
      
      # オプション解析
      aa_profile=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --aa)
            aa_profile="restricted"
            shift
            ;;
          --aa=*)
            aa_profile="${1#--aa=}"
            shift
            ;;
          *)
            break
            ;;
        esac
      done
      
      if [[ -n "$aa_profile" ]]; then
        # AppArmor適用
        exec aa -p "$aa_profile" "$@"
      else
        # 通常実行
        exec "$real_nix" run "$@"
      fi
    else
      # 他のサブコマンドはそのまま
      exec "$real_nix" "$@"
    fi
  '';
}

# インストール
$ nix profile install .#nix-aa --priority 0

# 使用
$ nix run --aa nixpkgs#hello
$ nix run --aa=strict /home/nixos/bin/src/poc/tool
$ nix build nixpkgs#hello  # buildは通常通り
```

## 推奨: 段階的アプローチ

1. **現在**: `aa`コマンド（シンプル、明確）
2. **次**: nixエイリアス/ラッパー（nixコマンド統合）
3. **将来**: nixプラグイン（完全統合）

## 比較

| 方法 | メリット | デメリット |
|------|----------|------------|
| `aa`コマンド | シンプル、明確 | 別コマンド |
| nixエイリアス | nixコマンドのまま | 設定が必要 |
| 環境変数 | 柔軟 | 冗長 |
| プラグイン | 完全統合 | 実装が複雑 |

## 結論

`aa`は独立したコマンドですが、nixコマンドと統合する方法は複数あります。最もシンプルなのは：

```bash
# エイリアス設定
alias nixaa='nix run --impure --expr "(import /home/nixos/bin/src/poc/apparmor/flake.nix).packages.\${builtins.currentSystem}.aa"'

# 使用
$ nixaa nixpkgs#hello
$ nixaa /home/nixos/bin/src/poc/readability
```