{ config, pkgs, ... }:

{
  programs.home-manager.enable = true;

  home.username = "roccho";
  home.homeDirectory = "/home/roccho";

  home.packages = with pkgs; [
    helix
    zellij
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

    # (import ./rust.nix { inherit pkgs; }) # rust.nixが単一パッケージを返す場合
  ] 
  ++ (import ./nix.nix { inherit pkgs; })
  ++ (import ./rust.nix { inherit pkgs; })
  ++ (import ./go.nix { inherit pkgs; })
  ; # rust.nixがパッケージリストを返す場合、このように展開する

  home.file.".profilerc".text = ''
    # .bashrcの内容
    # export PATH="$HOME/.local/bin:$PATH"
    # alias ll='ls -la'
    # 他のエイリアスや環境変数を追加
    export EDITOR=hx
  '';
}
