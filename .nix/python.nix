{ pkgs, ... }:

let
  uv = pkgs.stdenv.mkDerivation {
    # curl -LsSf https://astral.sh/uv/install.sh | sh
  };
in
with pkgs; [
  
]
