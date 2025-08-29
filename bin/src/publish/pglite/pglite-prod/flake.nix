{
  description = "PGlite Production Worker with In-Memory Database";

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
            nodejs_20
            nodePackages.npm
            nodePackages.typescript
            nodePackages.typescript-language-server
          ];

          shellHook = ''
            echo "PGlite Production Environment"
            echo "Commands:"
            echo "  npm install - Install dependencies"
            echo "  npm run dev - Start local development server"
            echo "  npm run deploy - Deploy to Cloudflare Workers"
            node --version
            npm --version
          '';
        };
      });
}