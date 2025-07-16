{
  description = "VSS (Vector Similarity Search) with KuzuDB - JSON Schema based implementation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # Core dependencies
          kuzu
          numpy
          
          # JSON Schema validation
          jsonschema
          
          # Testing
          pytest
          pytest-cov
          
          # Development
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
          '';
        };
        
        apps = {
          # Main VSS service
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-service" ''
              cd ${./.}
              export PYTHONPATH="${./.}:$PYTHONPATH"
              exec ${pythonEnv}/bin/python -m vss_service "$@"
            ''}";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              export PYTHONPATH="${./.}:$PYTHONPATH"
              echo "Running VSS tests with JSON Schema validation..."
              exec ${pythonEnv}/bin/pytest -v "$@"
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