{
  description = "KuzuDB Full Text Search - Portable implementation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            uv
            stdenv.cc.cc.lib  # For compiled dependencies
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            echo "KuzuDB Full Text Search (FTS) Development Environment"
            echo ""
            echo "Setup: uv sync"
            echo "Run:   uv run python main.py"
            echo "Test:  uv run python -m pytest"
          '';
        };

        # Direct execution without entering shell
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScript "fts-index" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            ${pkgs.uv}/bin/uv run python main.py "$@"
          ''}";
        };

        # Create index
        apps.index = {
          type = "app";
          program = "${pkgs.writeShellScript "fts-create-index" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            ${pkgs.uv}/bin/uv run python -c "
from main import FullTextSearch
import sys
sys.path.append('/home/nixos/bin/src')
from db.kuzu.connection import get_connection

conn = get_connection()
fts = FullTextSearch(conn)
fts.install_extension()
fts.create_index(['title', 'content'])
print('FTS index created successfully')
"
          ''}";
        };

        # Search functionality
        apps.search = {
          type = "app";
          program = "${pkgs.writeShellScript "fts-search" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            if [ -z "$1" ]; then
              echo "Usage: nix run .#search -- \"your search query\""
              exit 1
            fi
            
            # Optional conjunctive flag
            CONJUNCTIVE="false"
            if [ "$2" = "--and" ] || [ "$2" = "--conjunctive" ]; then
              CONJUNCTIVE="true"
            fi
            
            cd ${./.}
            ${pkgs.uv}/bin/uv run python -c "
from main import FullTextSearch
import sys
sys.path.append('/home/nixos/bin/src')
from db.kuzu.connection import get_connection

query = '''$1'''
conjunctive = $CONJUNCTIVE
conn = get_connection()
fts = FullTextSearch(conn)

print(f'Searching for: {query} (mode: {\"AND\" if conjunctive else \"OR\"})')
results = fts.search(query, conjunctive=conjunctive)
for r in results:
    print(f\"\\n[Score: {r['score']:.3f}] {r['title']}\")
    print(f\"  {r['content'][:100]}...\")
"
          ''}";
        };

        # Batch index documents
        apps.index-directory = {
          type = "app";
          program = "${pkgs.writeShellScript "fts-index-directory" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            if [ -z "$1" ]; then
              echo "Usage: nix run .#index-directory -- /path/to/directory"
              exit 1
            fi
            
            cd ${./.}
            ${pkgs.uv}/bin/uv run python -c "
import os
import sys
from pathlib import Path
sys.path.append('/home/nixos/bin/src')
from main import FullTextSearch
from db.kuzu.connection import get_connection

directory = Path('''$1''')
if not directory.exists():
    print(f'Directory not found: {directory}')
    sys.exit(1)

conn = get_connection()
fts = FullTextSearch(conn)
fts.install_extension()

# Find all README files
readme_files = list(directory.rglob('README.md'))
print(f'Found {len(readme_files)} README files')

# Index them
for readme in readme_files:
    try:
        content = readme.read_text()
        rel_path = readme.relative_to(directory)
        # You would need to adapt this to your schema
        print(f'Indexing: {rel_path}')
    except Exception as e:
        print(f'Error indexing {readme}: {e}')
"
          ''}";
        };

        # Test command
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "fts-test" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            echo "Running FTS Tests..."
            ${pkgs.uv}/bin/uv sync --extra test
            ${pkgs.uv}/bin/uv run pytest test_fts.py -v "$@"
          ''}";
        };

        # Package for use by other flakes
        packages.fts-lib = pkgs.python311.pkgs.buildPythonPackage {
          pname = "kuzu-fts";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";
          
          propagatedBuildInputs = with pkgs.python311.pkgs; [
            # Let uv handle the actual dependencies
          ];
          
          # Skip dependency checks since uv manages them
          pythonImportsCheck = [];
        };
      });
}