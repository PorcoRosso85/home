{
  description = "Requirement Search POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/poc/search";
        
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          [ ! -d ".venv" ] && ${pkgs.uv}/bin/uv venv
          [ ! -f ".venv/.deps_installed" ] && ${pkgs.uv}/bin/uv pip install pytest && touch .venv/.deps_installed
          
          for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
            [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib"
          done
          
          ${script}
        '';
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ python311 uv patchelf stdenv.cc.cc.lib ruff ];
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${projectDir}
              export PYTHONPATH="${projectDir}/../../"
              # Use requirement/graph's venv which has kuzu
              exec /home/nixos/bin/src/requirement/graph/.venv/bin/python -m pytest -v
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${mkRunner "lint" ''
              exec ${pkgs.ruff}/bin/ruff check . "$@"
            ''}";
          };
          
          format = {
            type = "app";
            program = "${mkRunner "format" ''
              exec ${pkgs.ruff}/bin/ruff format . "$@"
            ''}";
          };
        };
      });
}