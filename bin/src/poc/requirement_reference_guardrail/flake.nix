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
          
          # Disable tests during build phase since tests/ directory is not in the package
          doCheck = false;
          
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
            # Run from current directory instead of nix store
            if [ -d "tests" ]; then
              export PYTHONPATH="src:$PYTHONPATH"
              ${pythonEnv}/bin/python -m pytest tests/ -v
            else
              echo "Error: tests directory not found. Please run from the project root directory."
              exit 1
            fi
          '';
          
          # Demo: Show guardrail enforcement
          demo = pkgs.writeShellScriptBin "demo-guardrail" ''
            set -e
            echo "Requirement Reference Guardrail Demo"
            echo "===================================="
            # Run from current directory instead of nix store
            if [ -f "scripts/example_enforcement.py" ]; then
              export PYTHONPATH="src:$PYTHONPATH"
              ${pythonEnv}/bin/python scripts/example_enforcement.py
            else
              echo "Error: demo script not found. Please run from the project root directory."
              exit 1
            fi
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