{
  description = "Pyright LSP CLI wrapper";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # CLI wrapper for pyright LSP
        pyrightCliWrapper = pkgs.writeShellScriptBin "pyright-cli" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          # Compile TypeScript wrapper
          ${pkgs.esbuild}/bin/esbuild \
            lsmcp-cli-wrapper.ts \
            --bundle \
            --platform=node \
            --outfile=/tmp/pyright-cli-wrapper.js
          
          # Run with pyright in PATH
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.nodejs}/bin/node /tmp/pyright-cli-wrapper.js "$@"
        '';
        
        # Test scripts
        testFindRefs = pkgs.writeShellScriptBin "test-find-refs" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Testing Find References ==="
          ${pyrightCliWrapper}/bin/pyright-cli find-refs test_good.py 7 7
        '';
        
        testRename = pkgs.writeShellScriptBin "test-rename" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Testing Rename Symbol ==="
          ${pyrightCliWrapper}/bin/pyright-cli rename test_good.py 7 7 ComputeEngine
        '';
        
        # Direct Python LSP interface
        pythonLsp = pkgs.writeShellScriptBin "python-lsp" ''
          #!${pkgs.bash}/bin/bash
          SCRIPT_DIR="$( cd "$( dirname "''${BASH_SOURCE[0]}" )" && pwd )"
          cd ${./.}
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python direct-lsp.py "$@"
        '';
        
      in
      {
        packages = {
          default = pythonLsp;
          pyright-cli = pyrightCliWrapper;
          test-find-refs = testFindRefs;
          test-rename = testRename;
          python = pythonLsp;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            pyright
            esbuild
            python3
          ];
          
          shellHook = ''
            echo "Pyright LSP CLI Development Environment"
            echo ""
            echo "Available commands:"
            echo "  pyright-cli find-refs <file> <line> <column>"
            echo "  pyright-cli rename <file> <line> <column> <new-name>"
            echo ""
            echo "Test commands:"
            echo "  nix run .#test-find-refs"
            echo "  nix run .#test-rename"
          '';
        };
        
        apps = {
          default = flake-utils.lib.mkApp {
            drv = pyrightCliWrapper;
          };
          
          test-find-refs = flake-utils.lib.mkApp {
            drv = testFindRefs;
          };
          
          test-rename = flake-utils.lib.mkApp {
            drv = testRename;
          };
          
          python = flake-utils.lib.mkApp {
            drv = pythonLsp;
          };
        };
      }
    );
}