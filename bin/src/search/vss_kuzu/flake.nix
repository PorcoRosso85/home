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
        
        # vss_kuzu パッケージ
        vssKuzu = pkgs.python312Packages.buildPythonPackage rec {
          pname = "vss_kuzu";
          version = "0.1.0";
          
          src = ./.;
          
          # setuptools形式でビルド
          pyproject = true;
          build-system = with pkgs.python312Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzuPyPackage
            numpy
            sentence-transformers
            sentencepiece  # Required by sentence-transformers tokenizer
            jsonschema
          ];
          
          pythonImportsCheck = [ "vss_kuzu" ];
          doCheck = false;
          
          meta = with pkgs.lib; {
            description = "Vector Similarity Search with KuzuDB";
            homepage = "https://github.com/your-org/vss-kuzu";
            license = licenses.mit;
          };
        };
        
        # Create Python environment
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
            # Base testing framework
            pytest
            
            # Core dependencies for VSS
            vssKuzu  # Our package
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
        # パッケージ出力
        packages = {
          default = pythonEnv;
          vssKuzu = vssKuzu;
          pythonEnv = pythonEnv;
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
            echo "  nix run .#test             - Run tests"
            echo "  nix run .#lint             - Run linter"
            echo "  nix run .#format           - Format code"
            echo "  nix run .#e2e              - Run e2e tests for import capability"
            echo "  nix run .#vss-extension    - Install VECTOR extension for a database"
            echo ""
            echo "Note: VECTOR extension must be installed for each database path"
            echo "Example: nix run .#vss-extension ./my_database"
            echo ""
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
          
          # E2E test runner
          e2e = {
            type = "app";
            program = "${pkgs.writeShellScript "e2e" ''
              cd /home/nixos/bin/src/search/vss_kuzu
              echo "Running e2e tests for external import capability..."
              ${pythonEnv}/bin/pytest -v test_e2e.py
            ''}";
          };
          
          # All tests
          test-all = {
            type = "app";
            program = "${pkgs.writeShellScript "test-all" ''
              cd /home/nixos/bin/src/search/vss_kuzu
              echo "Running all tests..."
              PYTHONPATH=. ${pythonEnv}/bin/pytest -v test_*.py
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
          
          # VECTOR extension installer
          vss-extension = {
            type = "app";
            program = "${pkgs.writeShellScript "vss-extension" ''
              echo "VSS VECTOR Extension Installer"
              echo "=============================="
              echo ""
              echo "This command installs the VECTOR extension for a specific KuzuDB database."
              echo ""
              echo "Usage: nix run .#vss-extension <db_path>"
              echo ""
              echo "Example:"
              echo "  nix run .#vss-extension ./my_database"
              echo "  nix run .#vss-extension /tmp/test_db"
              echo ""
              
              if [ $# -eq 0 ]; then
                echo "Error: Please provide a database path"
                echo ""
                echo "The VECTOR extension must be installed for each database individually."
                echo "For in-memory databases, the extension is installed at runtime."
                exit 1
              fi
              
              DB_PATH="$1"
              
              if [ ! -d "$DB_PATH" ]; then
                echo "Error: Database path '$DB_PATH' does not exist"
                echo "Please create the database first by running your application"
                exit 1
              fi
              
              echo "Installing VECTOR extension for database: $DB_PATH"
              
              ${pythonEnv}/bin/python -c "
import kuzu
import sys

try:
    db = kuzu.Database('$DB_PATH')
    conn = db.get_connection()
    
    print('Connected to database')
    
    # Install VECTOR extension
    conn.execute('INSTALL VECTOR')
    print('VECTOR extension installed')
    
    # Load extension to verify
    conn.execute('LOAD EXTENSION VECTOR')
    print('VECTOR extension loaded successfully')
    print()
    print('VECTOR extension is now available for: $DB_PATH')
    
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
            ''}";
          };
        };
      });
}