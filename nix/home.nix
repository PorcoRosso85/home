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
    #   initExtra = ''
    #     export TERM="xterm-256color"
    #     export COLORTERM="truecolor"
    #     eval "$(dircolors -b)"
    #     source "$HOME/.cargo/env" # 必要に応じて
    #   '';
    #   shellAliases = {
    #     ll = "ls -alF";
    #     la = "ls -A";
    #     l = "ls -CF";
    #     # その他のエイリアス
    #   };
    };

    # dircolors = { enable = true; }; # カスタムカラーが必要ならここで設定

    starship = {
      enable = true;
      # settings = { ... }; # starship の設定が必要ならここで追加
    };

    tmux = {
        enable = true;
    };

    direnv = {
      enable = true;
      enableBashIntegration = true; # see note on other shells below
      nix-direnv.enable = true;
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

    # aider-chat
  ] ++ (import ./language.nix { inherit pkgs; });

  home.file.".homerc".text = ''
    export EDITOR=hx
  '';
}