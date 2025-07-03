{
  description = "KuzuDB Native Vector Search - Portable implementation";

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
            echo "KuzuDB Vector Search (VSS) Development Environment"
            echo ""
            echo "Setup: uv sync"
            echo "Run:   uv run python main.py"
            echo "Test:  uv run python -m pytest"
          '';
        };

        # Direct execution without entering shell
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScript "vss-index" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            ${pkgs.uv}/bin/uv run python main.py "$@"
          ''}";
        };

        # Create index
        apps.index = {
          type = "app";
          program = "${pkgs.writeShellScript "vss-create-index" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            ${pkgs.uv}/bin/uv run python -c "
from main import NativeVectorSearch
from sentence_transformers import SentenceTransformer
import sys
sys.path.append('/home/nixos/bin/src')
from db.kuzu.connection import get_connection

conn = get_connection()
embedder = SentenceTransformer('all-MiniLM-L6-v2')
vss = NativeVectorSearch(conn, embedder)
vss.install_extension()
vss.create_index(rebuild=True)
print('VSS index created successfully')
"
          ''}";
        };

        # Search functionality
        apps.search = {
          type = "app";
          program = "${pkgs.writeShellScript "vss-search" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            if [ -z "$1" ]; then
              echo "Usage: nix run .#search -- \"your search query\""
              exit 1
            fi
            
            cd ${./.}
            ${pkgs.uv}/bin/uv run python -c "
from main import NativeVectorSearch
from sentence_transformers import SentenceTransformer
import sys
sys.path.append('/home/nixos/bin/src')
from db.kuzu.connection import get_connection

query = '''$1'''
conn = get_connection()
embedder = SentenceTransformer('all-MiniLM-L6-v2')
vss = NativeVectorSearch(conn, embedder)

print(f'Searching for: {query}')
results = vss.search(query, k=5)
for r in results:
    print(f\"\\n[Score: {r['score']:.3f}] {r['title']}\")
    print(f\"  {r['content'][:100]}...\")
"
          ''}";
        };

        # Test command
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "vss-test" ''
            set -e
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            cd ${./.}
            echo "Running VSS Tests..."
            ${pkgs.uv}/bin/uv sync --extra test
            ${pkgs.uv}/bin/uv run pytest test_vss.py -v "$@"
          ''}";
        };

        # Package for use by other flakes
        packages.vss-lib = pkgs.python311.pkgs.buildPythonPackage {
          pname = "kuzu-vss";
          version = "0.2.0";
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