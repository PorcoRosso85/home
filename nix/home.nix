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
    };

    # dircolors = { enable = true; }; # カスタムカラーが必要ならここで設定

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

    pnpm
    nodejs_22
    uv
    python311

    # aider-chat
  ] ++ (import ./language.nix { inherit pkgs; });

  home.file.".profile".text = ''
    source ~/.profile_
  '';
}
