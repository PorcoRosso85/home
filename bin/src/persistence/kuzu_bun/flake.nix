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

        devPkgs = with pkgs; [
          # HTTP server for browser examples
          python3
          # Development tools
          curl
          jq
        ];

      in {
        devShells.default = pkgs.mkShell {
          packages = nodePkgs ++ devPkgs;

          shellHook = ''
            echo "=€ KuzuDB Bun Environment Ready"
            echo ""
            echo "Available commands:"
            echo "  bun install          - Install dependencies"
            echo "  bun run test:node    - Test Node.js example"
            echo "  bun run test:browser - Start browser test server"
            echo "  bun run test:all     - Run all tests"
            echo ""
            echo "To start HTTP server for browser examples:"
            echo "  python -m http.server 8000"
            echo ""
          '';
        };

        packages = {
          default = pkgs.writeShellScriptBin "kuzu-bun-test" ''
            #!/usr/bin/env bash
            set -e

            echo ">ê Testing KuzuDB with Bun..."
            
            # Install dependencies
            if [ ! -d "node_modules" ]; then
              echo "=æ Installing dependencies..."
              bun install
            fi

            # Run Node.js example
            echo "=¥ Testing Node.js example..."
            bun examples/nodejs_example.js

            echo " All tests passed!"
          '';

          browser-server = pkgs.writeShellScriptBin "kuzu-browser-server" ''
            #!/usr/bin/env bash
            echo "< Starting browser test server on http://localhost:8000"
            echo "Open examples/browser_example.html or browser_in_memory.html in your browser"
            ${pkgs.python3}/bin/python -m http.server 8000
          '';
        };
      });
}