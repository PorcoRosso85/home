{
  description = "RedwoodSDK development environment";

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
            nodePackages.pnpm
            nodePackages.wrangler
            openssl
            pkg-config
            # Prisma engines for NixOS
            prisma-engines
            # Required for patchelf
            patchelf
            stdenv.cc.cc.lib
          ];

          shellHook = ''
            # Prisma engine paths for NixOS
            export PRISMA_SCHEMA_ENGINE_BINARY="${pkgs.prisma-engines}/bin/schema-engine"
            export PRISMA_QUERY_ENGINE_BINARY="${pkgs.prisma-engines}/bin/query-engine"
            export PRISMA_QUERY_ENGINE_LIBRARY="${pkgs.prisma-engines}/lib/libquery_engine.node"
            export PRISMA_FMT_BINARY="${pkgs.prisma-engines}/bin/prisma-fmt"
            export PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1
            
            # Set LD_LIBRARY_PATH for dynamic binaries
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Create patchelf script for workerd
            cat > patch-workerd.sh << 'EOF'
            #!/usr/bin/env bash
            WORKERD_PATH="node_modules/workerd/bin/workerd"
            if [ -f "$WORKERD_PATH" ]; then
              echo "Patching workerd binary for NixOS..."
              chmod +x "$WORKERD_PATH"
              patchelf --set-interpreter "$(cat $NIX_CC/nix-support/dynamic-linker)" "$WORKERD_PATH"
              patchelf --set-rpath "${pkgs.stdenv.cc.cc.lib}/lib" "$WORKERD_PATH"
              echo "✅ workerd binary patched successfully"
            fi
            EOF
            chmod +x patch-workerd.sh
            
            echo "🚀 RedwoodSDK development environment loaded"
            echo "   Node.js: $(node --version)"
            echo "   pnpm: $(pnpm --version)"
            echo ""
            echo "To enable full-stack development:"
            echo "  1. Run: pnpm install"
            echo "  2. Run: ./patch-workerd.sh"
            echo "  3. Run: pnpm run dev"
            echo ""
            echo "Production URL: https://my-app-dev.test-app-prod.workers.dev"
          '';
        };
      });
}