{ config, pkgs, lib, ... }:

{
  imports = [
    ./modules/packages.nix
  ];

  # Home Manager needs this
  home.username = "nixos";
  home.homeDirectory = "/home/nixos";
  home.stateVersion = "25.05";

  programs = {
    home-manager.enable = true;

    bash = {
      enable = true;
      initExtra = ''
        if [ -f "$HOME/.config/shell/main.sh" ]; then
          source "$HOME/.config/shell/main.sh"
        fi
      '';
    };

    starship = {
      enable = true;
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
  ];

  home.file.".profile".text = ''
    source ~/.profile_
  '';
}