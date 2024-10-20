{ config, pkgs, lib, ... }:

let
  # username = builtins.getEnv "USER";
  username = "roccho";
in
{
  programs.home-manager.enable = true;

  home.username = username;
  home.homeDirectory = "/home/${username}";

  home.packages = with pkgs; [
    helix
    tmux
    starship
    curl
    wget
    unzip
    git
    gh
    tre-command
    fzf
    ripgrep
    fd
    bat
    zoxide
    eza
    lazygit
    broot
    aider-chat


    # (import ./rust.nix { inherit pkgs; }) # rust.nixが単一パッケージを返す場合
  ] 
  ++ (import ./nix.nix { inherit pkgs; })
  ++ (import ./rust.nix { inherit pkgs; })
  ++ (import ./go.nix { inherit pkgs; })
  ++ (import ./python.nix { inherit pkgs; })
  ;

  home.file.".homerc".text = ''
    export EDITOR=hx
  '';
}
