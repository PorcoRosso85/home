{
  description = "VSS (Vector Similarity Search) with KuzuDB - JSON Schema based implementation";

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
            
            # JSON Schema validation
            jsonschema
            
            # Development tools
            pytest-cov
            black
            ruff
        ]);
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            uv
            ruff
            black
          ];
          
          shellHook = ''
            echo "VSS KuzuDB JSON Schema Implementation"
            echo "======================================"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test      - Run tests"
            echo "  nix run .#lint      - Run linter"
            echo "  nix run .#format    - Format code"
            echo "  nix run .#validate  - Validate JSON schemas"
            echo ""
            
            # No PYTHONPATH needed, testing pure flake input
          '';
        };
        
        apps = {
          # LLM-first entry point (default)
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-entry" ''
              cd ${./.}
              exec ${pythonEnv}/bin/python entry.py "$@"
            ''}";
          };
          
          # Run mode (JSON input)
          run = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-run" ''
              cd ${./.}
              exec ${pythonEnv}/bin/python entry.py run "$@"
            ''}";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run tests from the source directory
              cd /home/nixos/bin/src/search/vss_kuzu
              echo "Running VSS tests with JSON Schema validation..."
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
          
          # JSON Schema validator
          validate = {
            type = "app";
            program = "${pkgs.writeShellScript "validate" ''
              cd ${./.}
              echo "Validating JSON schemas..."
              ${pythonEnv}/bin/python -c "
import json
import jsonschema
from pathlib import Path

schemas = ['input.schema.json', 'output.schema.json']
for schema_file in schemas:
    path = Path(schema_file)
    if path.exists():
        with open(path) as f:
            schema = json.load(f)
        try:
            jsonschema.Draft7Validator.check_schema(schema)
            print(f'✓ {schema_file} is valid')
        except jsonschema.SchemaError as e:
            print(f'✗ {schema_file} has errors: {e}')
            exit(1)
    else:
        print(f'✗ {schema_file} not found')
        exit(1)
"
            ''}";
          };
        };
      });
}