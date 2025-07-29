{
  description = "Requirement Reference Guardrail - Security standard compliance enforcement";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
        
        # Build guardrail package
        guardrailPackage = pythonPackages.buildPythonPackage {
          pname = "requirement-reference-guardrail";
          version = "0.1.0";
          src = pkgs.lib.cleanSource ./.;
          pyproject = true;
          
          build-system = with pythonPackages; [
            setuptools
            wheel
          ];
          
          dependencies = with pythonPackages; [
            pyarrow  # For Arrow Table handling
            kuzu
          ];
          
          nativeCheckInputs = with pythonPackages; [
            pytest
            pytest-cov
            pytest-asyncio
          ];
          
          checkPhase = ''
            pytest tests/ -v
          '';
          
          pythonImportsCheck = [
            "guardrail"
          ];
        };
        
        # Python environment with all dependencies
        pythonEnv = python.withPackages (ps: [
          guardrailPackage
          ps.pytest
          ps.ipython
        ]);
        
      in
      {
        packages = {
          default = guardrailPackage;
          python-env = pythonEnv;
          
          # Test runner
          test = pkgs.writeShellScriptBin "test-guardrail" ''
            set -e
            echo "Running Requirement Reference Guardrail tests..."
            cd ${self}
            export PYTHONPATH="${self}/src:$PYTHONPATH"
            ${pythonEnv}/bin/python -m pytest tests/ -v
          '';
          
          # Demo: Show guardrail enforcement
          demo = pkgs.writeShellScriptBin "demo-guardrail" ''
            set -e
            echo "Requirement Reference Guardrail Demo"
            echo "===================================="
            cd ${self}
            export PYTHONPATH="${self}/src:$PYTHONPATH"
            ${pythonEnv}/bin/python scripts/example_enforcement.py
          '';
        };
        
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.demo}/bin/demo-guardrail";
          };
          
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-guardrail";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            # Development tools
            python312Packages.black
            python312Packages.isort
            python312Packages.ruff
            python312Packages.mypy
            python312Packages.ipython
          ];
          
          shellHook = ''
            echo "Requirement Reference Guardrail Development Shell"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test         - Run all tests"
            echo "  nix run .#demo         - Run guardrail enforcement demo"
            echo ""
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
          '';
        };
      });
}