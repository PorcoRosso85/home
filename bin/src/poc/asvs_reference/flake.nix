{
  description = "ASVS Reference Management POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu_py.url = "path:../../persistence/kuzu_py";
    
    # OWASP ASVS source repository
    asvs-source = {
      url = "github:OWASP/ASVS";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, kuzu_py, asvs-source }:
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
          requests  # ASVS fetcher用
          numpy     # KuzuDB get_as_df()用
          pandas    # DataFrame操作用
        ];
        
        # Import kuzu_py as a local dependency
        kuzuPyPackage = kuzu_py.packages.${system}.default;
        
        # Python environment with all dependencies
        pythonEnv = python.withPackages (ps: pythonDeps ++ [ kuzuPyPackage ]);
        
        # ASVS 5.0 data from GitHub
        asvs5Data = pkgs.runCommand "asvs-5.0-data" {} ''
          mkdir -p $out/en
          # Copy markdown files from ASVS repository
          cp -r ${asvs-source}/5.0/en/*.md $out/en/
          echo "ASVS 5.0 data copied to $out"
        '';
        
      in
      {
        packages = {
          default = pythonEnv;
          
          # Test runner
          test = pkgs.writeShellScriptBin "test-asvs-reference" ''
            set -e
            echo "Running ASVS Reference tests..."
            cd ${self}
            export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
            ${pythonEnv}/bin/python -m pytest test_*.py -v
          '';
          
          # Demo for guardrails
          demo-guardrails = pkgs.writeShellScriptBin "demo-guardrails" ''
            set -e
            echo "Running ASVS guardrails demo..."
            cd ${self}
            export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
            ${pythonEnv}/bin/python demo_guardrails.py
          '';
          
          # Demo for mandatory references
          demo-mandatory = pkgs.writeShellScriptBin "demo-mandatory-references" ''
            set -e
            echo "Running mandatory references demo..."
            cd ${self}
            export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
            ${pythonEnv}/bin/python demo_mandatory_references.py
          '';
          
          # CLI for ASVS loader
          cli = pkgs.writeShellScriptBin "asvs-loader" ''
            set -e
            cd ${self}
            export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
            ${pythonEnv}/bin/python asvs_loader.py "$@"
          '';
          
          # Fetch ASVS 5.0 data from GitHub
          fetch-asvs5 = pkgs.writeShellScriptBin "fetch-asvs5" ''
            set -e
            echo "Fetching ASVS 5.0 data from GitHub..."
            cd ${self}
            export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
            export ASVS_SOURCE_PATH="${asvs5Data}"
            ${pythonEnv}/bin/python scripts/fetch_asvs_5.0.py
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
          
          fetch-asvs5 = {
            type = "app";
            program = "${self.packages.${system}.fetch-asvs5}/bin/fetch-asvs5";
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
            echo "  nix run .#fetch-asvs5       - Fetch ASVS 5.0 data from GitHub"
            echo ""
            echo "Python environment with pytest, pyyaml, jinja2, kuzu, and kuzu_py available"
          '';
        };
      });
}