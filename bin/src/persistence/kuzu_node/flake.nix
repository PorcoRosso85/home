{
  description = "KuzuDB and kuzu-wasm for Node.js runtime";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        nodePkgs = with pkgs; [
          nodejs_22  # Active LTS (2025年8月現在の推奨)
          # nodejs_20  # Maintenance LTS (レガシー環境用)
          # nodejs  # デフォルト版
        ];

      in {
        devShells.default = pkgs.mkShell {
          packages = nodePkgs;

          shellHook = ''
            echo "KuzuDB Node.js Environment Ready"
            echo ""
            echo "Available commands:"
            echo "  npm install          - Install dependencies"
            echo "  npm test             - Run tests"
            echo ""
          '';
        };

        packages = {
          default = pkgs.writeShellScriptBin "kuzu-node-test" ''
            #!/usr/bin/env bash
            set -e

            echo "Testing KuzuDB with Node.js..."
            
            # Install dependencies
            if [ ! -d "node_modules" ]; then
              echo "Installing dependencies..."
              npm install
            fi

            # Run tests
            echo "Running tests..."
            npm test

            echo "All tests passed!"
          '';
        };
      });
}