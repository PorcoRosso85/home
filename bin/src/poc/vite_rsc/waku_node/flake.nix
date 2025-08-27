{
  description = "Waku base environment for Cloudflare Workers deployment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        nodejs = pkgs.nodejs_22;
        
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            nodejs.pkgs.npm
            nodejs.pkgs.pnpm
            wrangler
          ];

          shellHook = ''
            echo "Waku base environment loaded"
            echo "Node: $(node --version)"
            echo "Wrangler: $(wrangler --version)"
            echo ""
            echo "This is a base environment for Waku + Cloudflare Workers"
            echo "Use this flake as input in your derivative projects"
          '';
        };

        packages = {
          build = pkgs.writeShellScriptBin "waku-build" ''
            set -e
            echo "Building Waku application..."
            
            # Install dependencies if needed
            if [ ! -d "node_modules" ]; then
              echo "Installing dependencies..."
              ${nodejs}/bin/npm install
            fi
            
            # Build with Cloudflare support
            ${nodejs}/bin/npx waku build --with-cloudflare
            
            echo "Build complete. Output in ./dist/"
          '';

          deploy = pkgs.writeShellScriptBin "waku-deploy" ''
            set -e
            echo "Deploying to Cloudflare Workers..."
            
            # Build first
            ${self.packages.${system}.build}/bin/waku-build
            
            # Deploy using wrangler
            ${pkgs.wrangler}/bin/wrangler deploy
            
            echo "Deployment complete!"
          '';
        };

        lib = {
          wakuConfig = ./waku.config.ts;
          packageJson = ./package.json;
        };
      });
}