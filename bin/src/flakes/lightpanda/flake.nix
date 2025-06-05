{
  description = "LightPanda browser (prebuilt binary)";
  
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "lightpanda";
          version = "nightly";
          
          src = pkgs.fetchurl {
            url = "https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux";
            hash = "sha256-C52fxcaHtjN/rgH0mJ5Uc/DkszaS8witABORDNiBvbY=";
          };
          
          dontUnpack = true;
          
          nativeBuildInputs = with pkgs; [ autoPatchelfHook ];
          buildInputs = with pkgs; [ gcc.cc.lib ];
          
          installPhase = ''
            mkdir -p $out/bin
            cp $src $out/bin/lightpanda
            chmod +x $out/bin/lightpanda
          '';
        };
      });
}