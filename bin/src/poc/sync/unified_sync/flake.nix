{
  description = "Unified Sync - KuzuDB WASM + WebSocket + Event Store";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
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
            # Deno for server and tests
            deno
            
            # Node.js for KuzuDB WASM compatibility
            nodejs_20
            nodePackages.pnpm
            
            # Playwright for E2E browser tests
            chromium
            
            # Development tools
            jq
            curl
            websocat  # WebSocket testing
          ];

          shellHook = ''
            echo "🔄 Unified Sync Development Environment"
            echo "====================================="
            echo ""
            echo "📦 Available tools:"
            echo "  - Deno ${pkgs.deno.version}"
            echo "  - Node.js ${pkgs.nodejs_20.version}"
            echo "  - pnpm (ESM package manager)"
            echo "  - Chromium (for Playwright)"
            echo "  - websocat (WebSocket testing)"
            echo ""
            echo "🧪 Test commands:"
            echo "  deno test                    - Run all tests"
            echo "  deno test --watch           - Watch mode"
            echo "  deno run --allow-all server.ts - Start server"
            echo ""
            
            # Playwright executable path
            export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=${pkgs.chromium}/bin/chromium
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
          '';
        };
      });
}