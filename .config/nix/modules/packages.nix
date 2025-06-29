{ pkgs, ... }:

{
  home.packages = with pkgs; [
    # Nix tools
    nixd
    nixfmt-rfc-style
    
    # Language servers and tools
    marksman
    rustup
    go
  ];
}