{
  description = "Detect differences in directory lists";

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
        ]);

        search-diffs = pkgs.writeScriptBin "search_diffs" ''
          #!${pythonEnv}/bin/python
          import sys
          import os
          import argparse
          from pathlib import Path

          def load_previous_state(state_file):
              """Load previous directory list from state file"""
              if not os.path.exists(state_file):
                  return set()
              
              with open(state_file, 'r') as f:
                  return set(line.strip() for line in f if line.strip())

          def save_current_state(state_file, directories):
              """Save current directory list to state file"""
              with open(state_file, 'w') as f:
                  for directory in sorted(directories):
                      f.write(directory + '\n')

          def detect_diffs(previous, current):
              """Detect differences between two sets of directories"""
              added = current - previous
              deleted = previous - current
              unchanged = current & previous
              
              return added, deleted, unchanged

          def main():
              parser = argparse.ArgumentParser(description='Detect directory differences')
              parser.add_argument('--state-file', default='.dirstate',
                                  help='State file to store directory list')
              parser.add_argument('--format', choices=['simple', 'json'], default='simple',
                                  help='Output format')
              args = parser.parse_args()
              
              # Read current directories from stdin
              current = set()
              for line in sys.stdin:
                  line = line.strip()
                  if line:
                      current.add(line)
              
              # Load previous state
              previous = load_previous_state(args.state_file)
              
              # Detect differences
              added, deleted, unchanged = detect_diffs(previous, current)
              
              # Output differences
              if args.format == 'simple':
                  for path in sorted(added):
                      print(f"+ {path}")
                  for path in sorted(deleted):
                      print(f"- {path}")
                  # Optionally output unchanged
                  # for path in sorted(unchanged):
                  #     print(f"= {path}")
              elif args.format == 'json':
                  import json
                  output = {
                      'added': sorted(added),
                      'deleted': sorted(deleted),
                      'unchanged': sorted(unchanged)
                  }
                  print(json.dumps(output))
              
              # Save current state
              save_current_state(args.state_file, current)

          if __name__ == "__main__":
              main()
        '';
      in
      {
        packages.default = search-diffs;
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            search-diffs
          ];
          
          shellHook = ''
            echo "search_diffs development environment"
            echo "Commands:"
            echo "  search_diffs - Detect directory differences"
            echo ""
            echo "Example:"
            echo "  find . -type d | search_diffs"
            echo "  find . -type d | search_diffs --state-file=.dirstate"
          '';
        };
      });
}