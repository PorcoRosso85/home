{
  description = "RedwoodSDK development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    duckdb-wasm.url = "path:../wasm/duckdb";
  };

  outputs = { self, nixpkgs, flake-utils, duckdb-wasm }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        checks = {
          asset-check = pkgs.runCommand "duckdb-asset-check" {} ''
            echo "Checking DuckDB WASM assets..."
            
            # Check if assets exist
            if [ ! -d "${duckdb-wasm.packages.${system}.assets}/wasm/duckdb" ]; then
              echo "ERROR: DuckDB assets directory not found"
              exit 1
            fi
            
            # Check for required files
            for file in duckdb-mvp.wasm duckdb-browser-mvp.worker.js duckdb-browser.mjs; do
              if [ ! -f "${duckdb-wasm.packages.${system}.assets}/wasm/duckdb/$file" ]; then
                echo "ERROR: Required file $file not found"
                exit 1
              fi
            done
            
            echo "✅ All required DuckDB WASM assets found"
            
            # Check file sizes (ensure they're not empty)
            wasm_size=$(stat -c%s "${duckdb-wasm.packages.${system}.assets}/wasm/duckdb/duckdb-mvp.wasm")
            if [ "$wasm_size" -lt 1000000 ]; then
              echo "ERROR: WASM file seems too small: $wasm_size bytes"
              exit 1
            fi
            
            echo "✅ WASM file size OK: $wasm_size bytes"
            echo "Asset check completed successfully" > $out
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_22
            nodePackages.pnpm
            # wrangler removed - use 'pnpm run wrangler' command instead
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
            
            # DuckDB WASM assets are served from R2, no local linking needed
            echo "🦆 DuckDB WASM assets configured for R2 serving"
            
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

        checks = {
          duckdb-assets = pkgs.runCommand "check-duckdb-assets" {} ''
            # Check that DuckDB WASM assets are available
            if [ -d "${duckdb-wasm.packages.${system}.assets}/wasm/duckdb" ]; then
              echo "✓ DuckDB assets found in Nix store" > $out
            else
              echo "✗ DuckDB assets not found" >&2
              exit 1
            fi
            
            # Verify key files exist
            for file in duckdb-mvp.wasm duckdb-browser-mvp.worker.js; do
              if [ -f "${duckdb-wasm.packages.${system}.assets}/wasm/duckdb/$file" ]; then
                echo "✓ Found $file" >> $out
              else
                echo "✗ Missing $file" >&2
                exit 1
              fi
            done
          '';
        };
      });
}