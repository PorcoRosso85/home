{
  description = "Vite RSC POC with Node.js runtime";

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
          packages = [
            pkgs.nodejs
            pkgs.nodePackages.npm
          ];
          
          shellHook = ''
            echo "==> Vite RSC POC Environment"
            echo "==> Node.js $(node --version)"
            echo "==> npm $(npm --version)"
            echo ""
            echo "Available commands:"
            echo "  npm install    - Install dependencies"
            echo "  npm run dev    - Start development server"
            echo "  npm run build  - Build for production"
            echo "  npm test       - Run tests"
            echo ""
            
            # Check if dependencies are installed
            if [ ! -d "node_modules" ]; then
              echo "Warning: Dependencies not installed. Run 'npm install' first."
            fi
          '';
        };
      });
}