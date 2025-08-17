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
            nodejs_20
            nodePackages.pnpm
          ];

          shellHook = ''
            echo "=ƒ Kuzu WASM + Vite + React ∞É"
            echo "=Ê pnpm install - ùX¢¬§Ûπ»¸Î"
            echo "=Ä pnpm dev - ãzµ¸–¸w’ (http://localhost:3000)"
            echo ""
            echo "’\∫ç"
            echo "1. ÷È¶∂≥ÛΩ¸Î (F12) gKuzuÌ∞∫ç"
            echo "2. ;bkØ®ÍPúh:"
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