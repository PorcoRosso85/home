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
          buildInputs = [
            nodejs
            pkgs.wrangler
          ];

          shellHook = ''
            echo "Waku base environment loaded"
            echo "Node: $(${nodejs}/bin/node --version)"
            echo "Wrangler: $(${pkgs.wrangler}/bin/wrangler --version)"
            echo ""
            echo "This is a base environment for Waku + Cloudflare Workers"
            echo "Use this flake as input in your derivative projects"
          '';
        };

        packages = {
          build = pkgs.writeShellScriptBin "waku-build" ''
            set -e
            echo "Building Waku application..."
            
            # Copy base infrastructure files if not present
            echo "Setting up infrastructure files from base..."
            
            [ ! -f "package.json" ] && cp ${./package.json} package.json
            [ ! -f "waku.config.ts" ] && cp ${./waku.config.ts} waku.config.ts
            [ ! -f "waku.hono-enhancer.ts" ] && cp ${./waku.hono-enhancer.ts} waku.hono-enhancer.ts
            [ ! -f "waku.cloudflare-middleware.ts" ] && cp ${./waku.cloudflare-middleware.ts} waku.cloudflare-middleware.ts
            [ ! -f "waku.cloudflare-dev-server.ts" ] && cp ${./waku.cloudflare-dev-server.ts} waku.cloudflare-dev-server.ts
            [ ! -f "postcss.config.js" ] && cp ${./postcss.config.js} postcss.config.js
            [ ! -f "tsconfig.json" ] && cp ${./tsconfig.json} tsconfig.json
            
            # Install dependencies if needed
            if [ ! -d "node_modules" ]; then
              echo "Installing dependencies..."
              ${nodejs}/bin/npm install
            fi
            
            # Build with Cloudflare support
            PATH=${nodejs}/bin:$PATH ${nodejs}/bin/npx waku build --with-cloudflare
            
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