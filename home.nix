{ config, pkgs, ... }:

{
  programs.home-manager.enable = true;

  home.username = "user";
  # home.homeDirectory = "/home/roccho";

  home.packages = [
    pkgs.git
    # 他に必要なパッケージを追加
  ];

  home.file.".bashrc".text = ''
    # .bashrcの内容
    # export PATH="$HOME/.local/bin:$PATH"
    # alias ll='ls -la'
    # 他のエイリアスや環境変数を追加
    export EDITOR=hx
  '';
}
