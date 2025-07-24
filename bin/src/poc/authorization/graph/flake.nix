{
  description = "KuzuDB-based Authorization Graph POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          kuzu
          pytest
          pytest-asyncio
          pytest-cov
          black
          mypy
          ruff
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            kuzu
          ];

          shellHook = ''
            echo "KuzuDB Authorization Graph POC Development Environment"
            echo "Python: $(python --version)"
            echo "Run tests with: nix run .#test"
          '';
        };

        packages = {
          default = pkgs.python311Packages.buildPythonPackage {
            pname = "auth-graph";
            version = "0.1.0";
            src = ./.;
            
            propagatedBuildInputs = with pkgs.python311Packages; [
              kuzu
            ];
            
            checkInputs = with pkgs.python311Packages; [
              pytest
              pytest-asyncio
              pytest-cov
            ];
            
            pythonImportsCheck = [ "auth_graph" ];
          };
        };

        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              export PYTHONPATH="$PWD/src:$PYTHONPATH"
              ${pythonEnv}/bin/pytest tests/ -v --cov=src --cov-report=term-missing
            ''}";
          };

          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format-code" ''
              ${pythonEnv}/bin/black src/ tests/
              ${pythonEnv}/bin/ruff check src/ tests/ --fix
            ''}";
          };

          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint-code" ''
              ${pythonEnv}/bin/black --check src/ tests/
              ${pythonEnv}/bin/ruff check src/ tests/
              ${pythonEnv}/bin/mypy src/
            ''}";
          };
        };
      });
}