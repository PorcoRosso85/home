{ pkgs, ... }:

let
  volta = pkgs.stdenv.mkDerivation {
    # curl https://get.volta.sh | bash
  };
in

with pkgs; [
  nodePackages.pnpm
  fnm
  biome
  typescript-language-server
]
