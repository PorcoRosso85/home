{
  description = "README Graph - 構造化READMEシステム";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Core
          jsonschema
          pydantic
          
          # KuzuDB
          kuzu
          
          # Testing & Development
          pytest
          pytest-cov
          ipython
          
          # Utilities
          rich
          typer
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            kuzu
            ruff
            mypy
            jq
          ];
          
          shellHook = ''
            echo "README Graph Development Environment"
            echo "Python $(python --version)"
            echo "KuzuDB CLI: kuzu_shell"
            echo "KuzuDB Python: import kuzu"
          '';
        };
        
        packages.default = pkgs.writeScriptBin "readme-graph" ''
          #!${pkgs.stdenv.shell}
          exec ${pythonEnv}/bin/python "$@"
        '';
      });
}