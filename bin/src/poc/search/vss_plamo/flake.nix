{
  description = "Ruri v3 + KuzuDB Vector Search POC";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python311
            uv
            stdenv.cc.cc.lib
            zlib
          ];
          
          shellHook = ''
            echo "Ruri v3 + KuzuDB VSS POC環境"
            echo "使用方法: nix run .#run"
            export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
          '';
        };
        
        apps.run = {
          type = "app";
          program = "${pkgs.writeShellScript "run-poc" ''
            export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
            export TMPDIR=/tmp
            cd /home/nixos/bin/src/poc/search/vss_plamo
            ${pkgs.uv}/bin/uv run python main_v2.py
          ''}";
        };
      });
}