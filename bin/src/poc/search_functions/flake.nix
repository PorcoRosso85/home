{
  description = "Extract directory paths from ctags JSON output";

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

        search-functions = pkgs.writeScriptBin "search_functions" ''
          #!${pythonEnv}/bin/python
          import sys
          import json
          from pathlib import Path

          def extract_directories():
              """Extract unique directory paths from ctags JSON input"""
              directories = set()
              
              for line in sys.stdin:
                  line = line.strip()
                  if not line:
                      continue
                  
                  try:
                      data = json.loads(line)
                      if 'path' in data:
                          # Get directory from file path
                          dir_path = str(Path(data['path']).parent)
                          if dir_path != '.':
                              directories.add(dir_path)
                          else:
                              # Add current directory
                              directories.add('.')
                  except json.JSONDecodeError:
                      # Skip invalid JSON lines
                      continue
              
              # Output sorted directory paths
              for directory in sorted(directories):
                  print(directory)

          if __name__ == "__main__":
              extract_directories()
        '';
      in
      {
        packages.default = search-functions;
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            universal-ctags
            search-functions
          ];
          
          shellHook = ''
            echo "search_functions development environment"
            echo "Commands:"
            echo "  search_functions - Extract directories from ctags JSON"
            echo "  ctags --output-format=json - Generate ctags JSON"
            echo ""
            echo "Example:"
            echo "  universal-ctags -R --output-format=json . | search_functions"
          '';
        };
      });
}