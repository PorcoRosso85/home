# Unix的パイプライン哲学でのAppArmor実装

## 要望

- **常時適用ではない**
- **使いたいときだけ使う**
- **Unixパイプライン的な柔軟性**

## 実現可能な方法

### 1. コマンドラインラッパー（最もUnix的）

```bash
# 使いたいときだけ明示的に
$ aa-run github:some/flake
$ aa-run --profile=strict github:untrusted/tool

# 通常実行も可能
$ nix run github:some/flake  # AppArmorなし
```

実装：
```nix
# aa-runコマンドを提供
{
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "aa-run" ''
      profile="''${AA_PROFILE:-default}"
      flake="$1"
      shift
      
      # flakeを一時的にビルド
      store_path=$(nix build --no-link --print-out-paths "$flake")
      
      # AppArmorで実行
      exec aa-exec -p "$profile" -- "$store_path/bin/"* "$@"
    '')
  ];
}
```

### 2. 環境変数による制御

```bash
# AppArmor有効化
$ export NIX_APPARMOR=1
$ nix run github:some/flake  # AppArmor適用

# 通常モード
$ unset NIX_APPARMOR
$ nix run github:some/flake  # AppArmorなし
```

### 3. Shellエイリアス/関数

```bash
# ~/.bashrc or ~/.zshrc
aa() {
  local flake="$1"
  shift
  nix run --override-input apparmor-wrapper path:/home/nixos/bin/src/poc/apparmor \
    -f '<apparmor-wrapper>' \
    --argstr targetFlake "$flake" \
    -- "$@"
}

# 使用例
$ aa github:some/flake --help
$ aa github:some/tool arg1 arg2
```

### 4. nix runのラッパー関数

```bash
# より自然な構文
nix-run-aa() {
  local profile="${AA_PROFILE:-default}"
  local flake="$1"
  shift
  
  # AppArmorラッパーflakeを通して実行
  nix run .#apparmor-wrapper -- \
    --flake "$flake" \
    --profile "$profile" \
    -- "$@"
}

# エイリアス
alias nraa='nix-run-aa'

# 使用例
$ nraa github:some/flake
$ AA_PROFILE=strict nraa github:untrusted/tool
```

## 真のパイプライン風実装

```bash
# パイプ記号は使えないが、Unix哲学は実現
$ nix eval github:some/flake --apply 'f: (import ./apparmor).wrap f'
$ nix run --expr '(import ./apparmor).wrap (builtins.getFlake "github:some/flake")'
```

## 推奨アプローチ

```nix
# flake.nix in apparmor POC
{
  apps.aa = {
    type = "app";
    program = pkgs.writeShellScript "aa" ''
      flake="$1"
      shift
      ${self.lib.wrapFlakeWithAppArmor {
        flake = builtins.getFlake "$flake";
        profileName = "default";
      }}/bin/* "$@"
    '';
  };
}
```

使用：
```bash
# シンプルで直感的
$ nix run .#aa github:some/flake
$ nix run .#aa -- --profile=strict github:some/tool

# またはインストール
$ nix profile install .#aa
$ aa github:some/flake
```

## まとめ

True Unix pipeline (`|`) は技術的に困難だが、Unix哲学の：
- **小さなツールを組み合わせる**
- **必要なときだけ使う**
- **シンプルなインターフェース**

は完全に実現可能。