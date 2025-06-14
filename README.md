# home for `<branchName> user`

## 

### create user on nixos / wsl2

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
    (fetchTarball "https://github.com/nix-community/nixos-vscode-server/tarball/master")
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";
  # vscode-remote-workaround.enable = true;


  environment.systemPackages = [
    pkgs.wget
    pkgs.helix
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

  programs.nix-ld = {
    enable = true;
    package = pkgs.nix-ld-rs; # only for NixOS 24.05
  };

  users.users.roccho = {
    isNormalUser = true;
    password = "roccho"; # set password up here
    # password = "$6$mKwV.T7nIO3yqW8k$3TWXPmb5zBMKK3.Uk3K1LEq40eOdh1RBQ0qBymmMzNAhjWxeaBbi3nN17lA/T5j/7kG8214xHFX3B/7bguzMn.";
    extraGroups = [ "wheels" ];
  };
  # https://github.com/sonowz/vscode-remote-wsl-nixos/blob/master/README.md

  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
  };

  # i18n.defaultLocale = "ja_JP.UTF-8";

  # unstableチャンネルからパッケージを取得
  environment.systemPackages = with nixpkgs.unstable; [
    wget
    curl
    git
    gh
    lazygit
    helix
    yazi

    duckdb

    pnpm
    uv
    nushell

    bash-language-server

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
    # podman = {
    #   enable = true;
    #   dockerCompat = true;
    # };
    docker = {
      enable = true;
    };
  };

  users.users = {
    # roccho = {
    #   isNormalUser = true;
    #   password = "roccho"; # set password up here
    #   extraGroups = [ "wheel" "podman" ];
    # };
    nixos = {
      extraGroups = [ "docker" ];
    };
  };

}

```

and then, in terminal...

`sudo nixos-rebuild switch`


### requirements before `nix build` and apply built home-manager configuration

<details>
<summary>without clone</summary>

* `nix build github:PorcoRosso85/home/<branchName>#homeConfigurations.roccho.activationPackage`
* `./result/activate`

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
