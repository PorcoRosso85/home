{ config, lib, pkgs, pkgs-unstable, ... }:

{
  imports = [
    # Hardware configuration will be added when available
    # ./hardware-configuration.nix
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";
  
  services = {
    vscode-server.enable = true;
    tailscale.enable = true;
    dbus = {
      enable = true;
      implementation = "dbus";
    };
  };
  
  wsl.wslConf.automount.root = "/mnt";
  wsl.wslConf.interop.appendWindowsPath = true;
  wsl.wslConf.network.generateHosts = true;
  
  system.stateVersion = "25.05";
  
  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
  };
  
  environment.systemPackages = with pkgs-unstable; [
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
  
  virtualisation.docker.enable = true;
  
  users.users.nixos = {
    extraGroups = [ "docker" ];
  };
}