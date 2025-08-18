{
  description = "Kuzu WASM + Vite + React minimal setup";

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
            nodejs_24
            nodePackages.pnpm
            chromium
          ];

          shellHook = ''
            echo "== Kuzu WASM + Vite + React =="
            echo "Commands:"
            echo "  pnpm install - Install dependencies"
            echo "  pnpm dev - Start dev server (http://localhost:5173)"
            echo ""
            echo "Environment:"
            echo "  Node.js: $(node --version)"
            echo "  Chromium: $(chromium --version | cut -d' ' -f1-2)"
            echo "  Chromium path: $(which chromium)"
            echo ""
            echo "Usage:"
            echo "1. Open browser console (F12) to see Kuzu WASM logs"
            echo "2. Check ping.cypher execution result"
            echo "3. For Playwright tests, use system chromium"
          '';
        };

        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "start" ''
            ${pkgs.nodePackages.pnpm}/bin/pnpm install
            ${pkgs.nodePackages.pnpm}/bin/pnpm dev
          ''}/bin/start";
        };
      });
}