# home for user `<branch name>`

## description

### create user on nixos(with wsl)

`/etc/nixos/configuration.nix`

```nix
❯ sudo cat /etc/nixos/configuration.nix
{ config, lib, pkgs, ... }:

let
  # nixpkgsのunstableブランチをインポート
  nixpkgs = import <nixpkgs> {
    system = "x86_64-linux"; # 必要なら他のアーキテクチャを指定
    overlays = [
      (self: super: {
        unstable = import (builtins.fetchTarball {
          url = "https://github.com/NixOS/nixpkgs/archive/nixpkgs-unstable.tar.gz";
        }) { inherit (super) system; };
      })
    ];
  };
in
{
  imports = [
    <nixos-wsl/modules>
    # /etc/nixos/modules/vscode.nix
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  # https://github.com/K900/vscode-remote-workaround/blob/main/vscode.nix
  # https://github.com/sonowz/vscode-remote-wsl-nixos/blob/master/README.md
  # vscode-remote-workaround.enable = true;

  system.stateVersion = "24.05";

  # i18n.defaultLocale = "ja_JP.UTF-8";

  # unstableチャンネルからパッケージを取得
  environment.systemPackages = with nixpkgs.unstable; [
    # ipafont

    wget
    curl
    git
    gh
    lazygit
    helix
    aichat
    aider-chat
    yazi

    chromium

  ];

  security.sudo.enable = true;
  security.sudo.extraRules = [
    {
      groups = [ "wheel" ];  # wheel グループを対象に
      commands = [
        {
          command = "ALL";  # すべてのコマンドを許可
          options = [ "SETENV" "NOPASSWD" ];  # パスワードなしで実行可能
        }
      ];
    }
  ];

  # programs.nix-ld = {
  #   enable = true;
  #   package = pkgs.nix-ld-rs; # only for NixOS 24.05
  # };

  programs = {
    tmux = {
      enable = true;
      clock24 = true; # 24時間表示にする
      # extraConfigで直接tmux.confに記述するのと同じことができる
      extraConfig = ''
        set -g status-bg black
        set -g status-fg white
        set-window-option -g window-status-current-format '#[fg=colour235,bg=colour27,bold] #I#[fg=colour235,bg=colour238]:#W#[fg=colour238,bg=colour235] '
      '';
      plugins = with pkgs.tmuxPlugins; [
        # tmux-sensible プラグインの追加例
        # sensible
      ];
    };
  };

  virtualisation = {
    podman = {
      enable = true;
      dockerCompat = true;
    };
  };

  users.users = {
    roccho = {
      isNormalUser = true;
      password = "roccho"; # set password up here
      extraGroups = [ "wheel" "podman" ];
    };
  };

  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
  };
}
```

### this file is for

1. configure the home with nix
   1. nix, home-manager
   2. git


### requirements before `nix build` and apply built home-manager configuration

<details>
<summary>without clone</summary>

* `nix build github:PorcoRosso85/home/branch_name#homeConfigurations.roccho.activationPackage`
</details>

<details>
<summary>with clone</summary>

* `git init`
* `git remote add origin https://github.com/PorcoRosso85/home.git`
* checkout to branch 'branch_name'
* `nix build .#homeConfigurations.roccho.activationPackage`
* `./result/activate`
</details>

### for integrating vscode into nixos
https://github.com/sonowz/vscode-remote-wsl-nixos/tree/master
