{
  description = "KuzuDB and kuzu-wasm for Bun runtime";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        nodePkgs = with pkgs; [
          nodejs_20
          bun
        ];

      in {
        devShells.default = pkgs.mkShell {
          packages = nodePkgs;

          shellHook = ''
            echo "KuzuDB Bun Environment Ready"
            echo ""
            echo "Available commands:"
            echo "  bun install          - Install dependencies"
            echo "  bun test             - Run tests"
            echo ""
          '';
        };

        packages = {
          default = pkgs.writeShellScriptBin "kuzu-bun-test" ''
            #!/usr/bin/env bash
            set -e

            echo "Testing KuzuDB with Bun..."
            
            # Install dependencies
            if [ ! -d "node_modules" ]; then
              echo "Installing dependencies..."
              bun install
            fi

            # Run tests
            echo "Running tests..."
            bun test

            echo "All tests passed!"
          '';
        };
      });
}