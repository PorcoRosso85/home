{ config, pkgs, lib, ... }:

let
  # username = builtins.getEnv "USER";
  username = "nixos";
in
{
  programs.home-manager.enable = true;

  home.username = username;
  home.homeDirectory = "/home/${username}";

  home.packages = with pkgs; [
    tmux
    starship
    unzip
    tre-command
    fzf
    ripgrep
    fd
    bat
    zoxide
    eza
    lazygit
    broot

    gcc
    # aider-chat

    # (import ./rust.nix { inherit pkgs; }) # rust.nixが単一パッケージを返す場合
  ] 
  ++ (import ./language.nix { inherit pkgs; })
  ;

  # ここにcargo, go, nodeツールをsourceするシェル設定をおいてもいいかもしれない
  home.file.".homerc".text = ''
    export EDITOR=hx
  '';
}
