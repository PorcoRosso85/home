{
  description = "Requirement Reference Guardrail - Security standard compliance enforcement";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # External POC dependencies
    asvs-reference.url = "path:../asvs_reference";
    embed.url = "path:../embed";
    kuzu-py.url = "path:../../persistence/kuzu_py";
    requirement-graph.url = "path:../../requirement/graph";
  };

  outputs = { self, nixpkgs, flake-utils, asvs-reference, embed, kuzu-py, requirement-graph }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
        
        # Get packages from external POCs
        asvsPackage = asvs-reference.packages.${system}.default;
        embedPackage = embed.packages.${system}.default;
        kuzuPackage = kuzu-py.packages.${system}.kuzuPy;
        
        # Build guardrail package
        guardrailPackage = pythonPackages.buildPythonPackage {
          pname = "requirement-reference-guardrail";
          version = "0.1.0";
          src = self;
          pyproject = true;
          
          build-system = with pythonPackages; [
            setuptools
            wheel
          ];
          
          dependencies = with pythonPackages; [
            asvsPackage
            embedPackage
            kuzuPackage
            pyarrow  # For Arrow Table handling
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
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnv}/bin/python -m pytest tests/ -v
          '';
          
          # Demo: Show guardrail enforcement
          demo = pkgs.writeShellScriptBin "demo-guardrail" ''
            set -e
            echo "Requirement Reference Guardrail Demo"
            echo "===================================="
            cd ${self}
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnv}/bin/python demo/demo_enforcement.py
          '';
          
          # Import ASVS data
          import-asvs = pkgs.writeShellScriptBin "import-asvs" ''
            set -e
            echo "Importing ASVS data into KuzuDB..."
            cd ${self}
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnv}/bin/python scripts/import_asvs.py "$@"
          '';
          
          # Coverage analysis
          coverage = pkgs.writeShellScriptBin "analyze-coverage" ''
            set -e
            echo "Analyzing security standard coverage..."
            cd ${self}
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnv}/bin/python scripts/analyze_coverage.py "$@"
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
          
          import-asvs = {
            type = "app";
            program = "${self.packages.${system}.import-asvs}/bin/import-asvs";
          };
          
          coverage = {
            type = "app";
            program = "${self.packages.${system}.coverage}/bin/analyze-coverage";
          };
        };
        
        # Export for other flakes
        lib = {
          inherit guardrailPackage;
          
          # Expose guardrail functions
          createGuardrailEnforcer = import ./src/guardrail_enforcer.nix {
            inherit pkgs asvsPackage embedPackage kuzuPackage;
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
            echo "  nix run .#import-asvs  - Import ASVS data into KuzuDB"
            echo "  nix run .#coverage     - Analyze security standard coverage"
            echo ""
            echo "External POCs integrated:"
            echo "  - asvs-reference: ASVS data provider (Arrow Tables)"
            echo "  - embed: Similarity search for duplicate detection"
            echo "  - kuzu-py: Graph database interface"
            echo ""
            export PYTHONPATH="$PWD:$PYTHONPATH"
          '';
        };
      });
}