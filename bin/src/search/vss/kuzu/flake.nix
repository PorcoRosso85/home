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
        
        # Create Python environment extending the base from python-flake
        # python-flake now only provides pytest
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
            # Base testing framework from python-flake
            pytest
            
            # Core dependencies for VSS
            kuzu
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
            stdenv.cc.cc.lib
            zlib
            blas
            lapack
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
            
            # Set PYTHONPATH to find persistence module
            export PYTHONPATH="/home/nixos/bin/src:${./.}:$PYTHONPATH"
            
            # Set LD_LIBRARY_PATH for NumPy C++ extensions
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.blas}/lib:${pkgs.lapack}/lib:$LD_LIBRARY_PATH"
          '';
        };
        
        apps = {
          # LLM-first entry point (default)
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-entry" ''
              cd ${./.}
              export PYTHONPATH="/home/nixos/bin/src:${./.}:$PYTHONPATH"
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.blas}/lib:${pkgs.lapack}/lib:$LD_LIBRARY_PATH"
              exec ${pythonEnv}/bin/python entry.py "$@"
            ''}";
          };
          
          # Run mode (JSON input)
          run = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-run" ''
              cd ${./.}
              export PYTHONPATH="/home/nixos/bin/src:${./.}:$PYTHONPATH"
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.blas}/lib:${pkgs.lapack}/lib:$LD_LIBRARY_PATH"
              exec ${pythonEnv}/bin/python entry.py run "$@"
            ''}";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run tests from the source directory, not from nix store
              cd /home/nixos/bin/src/search/vss/kuzu
              export PYTHONPATH="/home/nixos/bin/src:/home/nixos/bin/src/search/vss/kuzu:$PYTHONPATH"
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.blas}/lib:${pkgs.lapack}/lib:$LD_LIBRARY_PATH"
              # Fix numpy import issue
              export OPENBLAS_NUM_THREADS=1
              export MKL_NUM_THREADS=1
              export OMP_NUM_THREADS=1
              # Workaround for scipy numpy version issue
              export SCIPY_USE_PROPACK=1
              echo "Running VSS tests with JSON Schema validation..."
              exec ${pythonEnv}/bin/pytest -v tests/ "$@"
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