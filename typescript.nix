{ pkgs, ... }:

let
  volta = pkgs.stdenv.mkDerivation {
    # curl https://get.volta.sh | bash
  };
in

with pkgs; [
  
]
