{
  description = "@lazarv/react-server with Node.js 22";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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
            nodejs_22
            pnpm
            # Cloudflare Workers CLI
            nodePackages.wrangler
          ];

          shellHook = ''
            echo "=Ä @lazarv/react-server ◊ Node 22 ãz∞É"
            echo ""
            echo "Node.js: $(node --version)"
            echo "pnpm: $(pnpm --version)"
            echo ""
            echo "(Ô˝j≥ﬁÛ…:"
            echo "  pnpm install  - ùX¢¬n§Ûπ»¸Î"
            echo "  pnpm dev      - ãzµ¸–¸w’"
            echo "  pnpm build    - ◊Ì¿Ø∑ÁÛ”Î…"
            echo "  wrangler      - Cloudflare Workers CLI"
            echo ""
          '';
        };
      }
    );
}