{
  config,
  pkgs,
  lib,
  ...
}:

{
  imports = [
    ./modules/packages.nix
  ];

  # Home Manager needs this
  home = {
    username = "nixos";
    homeDirectory = "/home/nixos";
    stateVersion = "25.05";
    packages = with pkgs; [ ];
    file.".profile".text = ''
      [ -f ~/.profile_ ] && source ~/.profile_
    '';
  };

  programs = {
    home-manager.enable = true;

    nix-index.enable = true;

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

    git = {
      enable = true;
    };

    ssh = {
      enable = true;
    };
  };

  home.sessionVariables = {
    EDITOR = "hx";
    VISUAL = "hx";
  };

}
