{ config, pkgs, ... }:

{
  programs.home-manager.enable = true;

  home.username = "roccho";
  home.homeDirectory = "/home/roccho";

  home.packages = [
    # 他に必要なパッケージを追加
  ];

  home.file.".profilerc".text = ''
    # .bashrcの内容
    # export PATH="$HOME/.local/bin:$PATH"
    # alias ll='ls -la'
    # 他のエイリアスや環境変数を追加
    export EDITOR=hx
  '';
}
