{ config, pkgs, lib, ... }:

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
  ++ (import ./python.nix { inherit pkgs; })
  ; # rust.nixがパッケージリストを返す場合、このように展開する

  home.activation.installUV = lib.hm.dag.entryAfter ["writeBoundary"] ''
    UV_VERSION="0.4.6"
    if [ ! -f /usr/local/bin/uv ]; then
      echo "Installing UV version $UV_VERSION..."
      if curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | sh; then
        echo "UV installation successful."
      else
        echo "Failed to install UV. Please check your internet connection and try again."
        exit 1
      fi
    else
      echo "UV is already installed."
    fi
  '';

  home.file.".profilerc".text = ''
    # .bashrcの内容
    # export PATH="$HOME/.local/bin:$PATH"
    # alias ll='ls -la'
    # 他のエイリアスや環境変数を追加
    export EDITOR=hx
  '';
}
