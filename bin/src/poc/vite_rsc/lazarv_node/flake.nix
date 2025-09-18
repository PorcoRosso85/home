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
          ];

          shellHook = ''
            echo "@lazarv/react-server with Node 22 Development Environment"
            echo "==========================================================="
            echo "Node.js: $(node --version)"
            echo "pnpm: $(pnpm --version)"
            echo ""
            echo "Available commands:"
            echo "  pnpm install  - Install dependencies"
            echo "  pnpm dev      - Start development server"
            echo "  pnpm build    - Build for production"
            echo "==========================================================="
          '';
        };
      }
    );
}