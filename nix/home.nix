{ config, pkgs, lib, ... }:

let
  # username = builtins.getEnv "USER";
  # username = "nixos";
in
{
  programs = {
    home-manager.enable = true;

    bash = {
      enable = true;
      shellInit = ''
        export TERM="xterm-256color"
        export COLORTERM="truecolor"
        eval "$(dircolors -b)"
        # source "$HOME/.cargo/env"
      '';
      shellAliases = {
        ll = "ls -alF";
        la = "ls -A";
        l = "ls -CF";
        # ...
      };
      historyControl = "ignoreboth:erasedups";
    };

    dircolors = { enable = true; }; # カスタムカラーが必要ならここで設定

    starship = {
      enable = true;
      # settings = { ... }; # starship の設定が必要ならここで追加
    };

    tmux = {
        enable = true;
    };
  };

  home.packages = with pkgs; [
    unzip
    tre-command
    fzf
    ripgrep
    fd
    bat
    zoxide
    eza
    broot

    gcc
  ] ++ (import ./language.nix { inherit pkgs; });

  home.file.".homerc".text = ''
    export EDITOR=hx
  '';
}