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
    # nixos-vscode-serverをimportsに追加
    (builtins.fetchTarball "https://github.com/nix-community/nixos-vscode-server/tarball/master")
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";
  # WSL環境でsystemdを有効化
  wsl.nativeSystemd = true;
  # VSCode Serverの設定を有効にする
  services = {
    vscode-server = {
      enable = true;
      # お使いのNode.jsバージョンを指定（オプション）
      # nodejsPackage = pkgs.nodejs_22;
    };
    tailscale = {
      enable = true;
    };
    # D-Bus設定
    dbus = {
      enable = true;
      implementation = "dbus";
    };
  };
  
  # WSL関連の追加設定
  wsl.wslConf.automount.root = "/mnt";
  wsl.wslConf.interop.appendWindowsPath = true;
  wsl.wslConf.network.generateHosts = true;
  system.stateVersion = "25.05";
  
  # 以下は変更なし
  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
  };
  
  environment.systemPackages = with nixpkgs.unstable; [
    wget
    curl
    git
    gh
    lazygit
    helix
    yazi
    nushell
    bash-language-server
  ];
  
  security.sudo.enable = true;
  security.sudo.extraRules = [
    {
      groups = [ "wheel" ];
      commands = [
        {
          command = "ALL";
          options = [ "SETENV" "NOPASSWD" ];
        }
      ];
    }
  ];
  
  programs = {
    tmux = {
      enable = true;
      clock24 = true;
      extraConfig = ''
        set -g status-bg black
        set -g status-fg white
        set-window-option -g window-status-current-format '#[fg=colour235,bg=colour27,bold] #I#[fg=colour235,bg=colour238]:#W#[fg=colour238,bg=colour235] '
      '';
      plugins = with pkgs.tmuxPlugins; [
        # sensible
      ];
    };
  };
  
  virtualisation = {
    docker = {
      enable = true;
    };
  };
  
  users.users = {
    nixos = {
      extraGroups = [ "docker" ];
    };
  };
}
