{
  description = "Vite RSC POC with Bun runtime";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    bun-flake = {
      url = "path:/home/nixos/bin/src/flakes/bun";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, bun-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            bun-flake.packages.${system}.default
          ];
          
          shellHook = ''
            echo "==> Vite RSC POC Environment"
            echo "==> Bun $(bun --version)"
            echo ""
            echo "Available commands:"
            echo "  bun install    - Install dependencies"
            echo "  bun run dev    - Start development server"
            echo "  bun run build  - Build for production"
            echo "  bun test       - Run tests"
            echo ""
            
            # Check if dependencies are installed
            if [ ! -d "node_modules" ]; then
              echo "Warning: Dependencies not installed. Run 'bun install' first."
            fi
          '';
        };
      });
}