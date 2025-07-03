{
  description = "Build search index from directory differences";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          ps.kuzu
        ]);

        build-diffs = pkgs.writeScriptBin "build_diffs" ''
          #!${pythonEnv}/bin/python
          import sys
          import os
          import time
          import argparse
          from pathlib import Path
          import kuzu

          def init_database(db_path):
              """Initialize KuzuDB with schema"""
              db = kuzu.Database(db_path)
              conn = kuzu.Connection(db)
              
              # Create schema
              conn.execute("""
                  CREATE NODE TABLE IF NOT EXISTS Directory(
                      path STRING PRIMARY KEY,
                      has_readme BOOLEAN,
                      indexed_at INT64
                  )
              """)
              
              return db, conn

          def process_diff_line(line):
              """Parse diff line into operation and path"""
              line = line.strip()
              if not line:
                  return None, None
              
              if line.startswith('+ '):
                  return 'add', line[2:]
              elif line.startswith('- '):
                  return 'delete', line[2:]
              elif line.startswith('= '):
                  return 'unchanged', line[2:]
              else:
                  # Assume it's a plain path (for --init mode)
                  return 'add', line

          def check_readme(path):
              """Check if directory has README.md"""
              readme_files = ['README.md', 'readme.md', 'Readme.md']
              for readme in readme_files:
                  if os.path.exists(os.path.join(path, readme)):
                      return True
              return False

          def main():
              parser = argparse.ArgumentParser(description='Build search index from diffs')
              parser.add_argument('--db-path', default='search.db',
                                  help='KuzuDB database path')
              parser.add_argument('--init', action='store_true',
                                  help='Initialize mode (treat all as additions)')
              args = parser.parse_args()
              
              # Initialize database
              db, conn = init_database(args.db_path)
              
              # Process statistics
              added = 0
              deleted = 0
              start_time = time.time()
              
              # Process input
              for line in sys.stdin:
                  op, path = process_diff_line(line)
                  if not op or not path:
                      continue
                  
                  if op == 'add':
                      # Add directory to index
                      has_readme = check_readme(path)
                      conn.execute("""
                          CREATE (d:Directory {
                              path: $path,
                              has_readme: $has_readme,
                              indexed_at: $time
                          })
                      """, {
                          'path': path,
                          'has_readme': has_readme,
                          'time': int(time.time())
                      })
                      added += 1
                  
                  elif op == 'delete':
                      # Remove directory from index
                      conn.execute("""
                          MATCH (d:Directory {path: $path})
                          DELETE d
                      """, {'path': path})
                      deleted += 1
              
              # Report results
              elapsed = time.time() - start_time
              print(f"Added: {added} directories")
              print(f"Deleted: {deleted} directories")
              print(f"Updated index in {elapsed:.2f}s")

          if __name__ == "__main__":
              main()
        '';
      in
      {
        packages.default = build-diffs;
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            build-diffs
          ];
          
          shellHook = ''
            echo "build_diffs development environment"
            echo "Commands:"
            echo "  build_diffs - Build index from differences"
            echo ""
            echo "Examples:"
            echo "  echo '+ src/new' | build_diffs"
            echo "  find . -type d | build_diffs --init"
          '';
        };
      });
}