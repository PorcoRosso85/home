{
  description = "Persistence layer with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pkgs.python312Packages.kuzu
          numpy
          pandas
          pytest
          pytest-asyncio
          pydantic
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            echo "Persistence layer development environment"
            echo "Python version: $(python --version)"
            echo "Using Nix-provided kuzu package only"
          '';
        };
        
        packages.default = pythonEnv;
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            export PYTHONPATH="$PWD:$PYTHONPATH"
            ${pythonEnv}/bin/python test_minimal_kuzu.py
          ''}/bin/test";
        };
      });
}