{
  description = "VSS (Vector Similarity Search) with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Get kuzuPy package from kuzu-py-flake
        kuzuPyPackage = kuzu-py-flake.packages.${system}.kuzuPy;
        
        # Create Python environment
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
            # Base testing framework
            pytest
            
            # Core dependencies for VSS
            kuzu  # Base kuzu package
            kuzuPyPackage  # This provides kuzu_py module
            numpy
            scipy  # Required by sentence-transformers
            sentencepiece  # Required for tokenizer
            sentence-transformers
            torch
            
            
            # Development tools
            pytest-cov
            black
            ruff
        ]);
        
      in {
        packages.default = pkgs.python312Packages.buildPythonPackage {
          pname = "vss-kuzu";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzuPyPackage
            numpy
            sentence-transformers
            jsonschema
          ];
          
          pythonImportsCheck = [ "vss_kuzu" ];
          
          meta = with pkgs.lib; {
            description = "Vector Similarity Search with KuzuDB";
            homepage = "https://github.com/your-org/vss-kuzu";
            license = licenses.mit;
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            uv
            ruff
            black
          ];
          
          shellHook = ''
            echo "VSS KuzuDB Implementation"
            echo "========================"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test      - Run tests"
            echo "  nix run .#lint      - Run linter"
            echo "  nix run .#format    - Format code"
            echo ""
            
            # No PYTHONPATH needed, testing pure flake input
          '';
        };
        
        apps = {
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run tests from the source directory
              cd /home/nixos/bin/src/search/vss_kuzu
              echo "Running VSS tests..."
              # Run pytest with importlib import mode to avoid namespace conflicts
              PYTHONPATH=. exec ${pythonEnv}/bin/pytest -v --import-mode=importlib test_*.py "$@"
            ''}";
          };
          
          # Linter
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              cd ${./.}
              echo "Running linter..."
              ${pkgs.ruff}/bin/ruff check .
            ''}";
          };
          
          # Formatter
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              cd ${./.}
              echo "Formatting code..."
              ${pkgs.black}/bin/black .
              ${pkgs.ruff}/bin/ruff format .
            ''}";
          };
        };
      });
}