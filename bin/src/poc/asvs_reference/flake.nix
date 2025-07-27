{
  description = "ASVS Reference Management POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu_py.url = "path:../../persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu_py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        
        pythonPackages = python.pkgs;
        
        # Python dependencies
        pythonDeps = with pythonPackages; [
          pytest
          pytest-cov
          pyyaml
          jinja2
          kuzu
        ];
        
        # Import kuzu_py as a local dependency
        kuzuPyPackage = kuzu_py.packages.${system}.default;
        
        # Python environment with all dependencies
        pythonEnv = python.withPackages (ps: pythonDeps ++ [ kuzuPyPackage ]);
        
      in
      {
        packages = {
          default = pythonEnv;
          
          # Test runner
          test = pkgs.writeShellScriptBin "test-asvs-reference" ''
            set -e
            echo "Running ASVS Reference tests..."
            cd ${self}
            ${pythonEnv}/bin/python -m pytest test_*.py -v
          '';
          
          # Demo for guardrails
          demo-guardrails = pkgs.writeShellScriptBin "demo-guardrails" ''
            set -e
            echo "Running ASVS guardrails demo..."
            cd ${self}
            ${pythonEnv}/bin/python demo_guardrails.py
          '';
          
          # Demo for mandatory references
          demo-mandatory = pkgs.writeShellScriptBin "demo-mandatory-references" ''
            set -e
            echo "Running mandatory references demo..."
            cd ${self}
            ${pythonEnv}/bin/python demo_mandatory_references.py
          '';
          
          # CLI for ASVS loader
          cli = pkgs.writeShellScriptBin "asvs-loader" ''
            set -e
            cd ${self}
            ${pythonEnv}/bin/python asvs_loader.py "$@"
          '';
        };
        
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-asvs-reference";
          };
          
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-asvs-reference";
          };
          
          demo-guardrails = {
            type = "app";
            program = "${self.packages.${system}.demo-guardrails}/bin/demo-guardrails";
          };
          
          demo-mandatory = {
            type = "app";
            program = "${self.packages.${system}.demo-mandatory}/bin/demo-mandatory-references";
          };
          
          cli = {
            type = "app";
            program = "${self.packages.${system}.cli}/bin/asvs-loader";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            # Development tools
            python312Packages.black
            python312Packages.isort
            python312Packages.flake8
            python312Packages.mypy
            python312Packages.ipython
          ];
          
          shellHook = ''
            echo "ASVS Reference Management POC Development Shell"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test              - Run all tests"
            echo "  nix run .#demo-guardrails   - Run guardrails demo"
            echo "  nix run .#demo-mandatory    - Run mandatory references demo"
            echo "  nix run .#cli               - Run ASVS loader CLI"
            echo ""
            echo "Python environment with pytest, pyyaml, jinja2, kuzu, and kuzu_py available"
          '';
        };
      });
}