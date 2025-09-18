{
  description = "Publish workspace - Deployment targets orchestration with Turbo";

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
          packages = with pkgs; [
            nodejs_22
            nodePackages.npm
            turbo
          ];

          shellHook = ''
            echo "Publish workspace environment loaded"
            echo "Node: $(node --version)"
            echo "Turbo: $(turbo --version)"
            echo ""
            echo "Available commands:"
            echo "  turbo run build       - Build all packages"
            echo "  turbo run dev         - Start dev servers"
            echo "  turbo run typecheck   - Run TypeScript checks"
            echo ""
            echo "Filter examples:"
            echo "  turbo run build --filter=waku-init"
            echo "  turbo run build --filter='...[HEAD^]'"
          '';
        };
      }
    );
}