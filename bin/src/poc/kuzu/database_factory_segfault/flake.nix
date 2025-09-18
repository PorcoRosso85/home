{
  description = "POC for KuzuDB database factory segfault investigation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            uv
            patchelf
            stdenv.cc.cc.lib
          ];
        };
        
        apps = {
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${self}/README.md
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd /home/nixos/bin/src/poc/kuzu/database_factory_segfault
              
              # kuzuのSOファイルを修正
              for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
                [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib"
              done
              
              exec .venv/bin/pytest "$@"
            ''}";
          };
        };
      });
}