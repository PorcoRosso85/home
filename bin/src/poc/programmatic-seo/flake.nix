{
  description = "Programmatic SEO Phase 1.0 - Zero CF paste-only foundation";

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
            nodePackages.typescript
            esbuild
            miniserve  # For serve-examples
          ];

          shellHook = ''
            echo "Programmatic SEO Phase 1.0 Development Environment"
            echo "Node.js $(node --version)"
            echo "TypeScript $(tsc --version)"
            echo "esbuild $(esbuild --version)"
            echo ""
            echo "Available commands:"
            echo "  nix run .#check         - Type check (tsc --noEmit)"
            echo "  nix run .#build-snippet - Build ESM+IIFE snippets"
            echo "  nix run .#serve-examples - Serve examples for testing"
            echo ""
          '';
        };

        apps = {
          check = {
            type = "app";
            program = "${pkgs.writeShellScript "check" ''
              echo "Running TypeScript type check..."
              ${pkgs.nodePackages.typescript}/bin/tsc --noEmit 2>&1

              if [ $? -eq 0 ]; then
                echo "Type check passed - no errors found"
              else
                echo "Type check failed - see errors above"
                exit 1
              fi
            ''}";
          };

          build-snippet = {
            type = "app";
            program = "${pkgs.writeShellScript "build-snippet" ''
              echo "Building measurement snippet..."

              # Create dist directory
              mkdir -p dist/measurement

              # Build ESM version
              ${pkgs.esbuild}/bin/esbuild packages/measurement/snippet.ts \
                --bundle \
                --format=esm \
                --target=es2020 \
                --outfile=dist/measurement/snippet.esm.js

              # Build IIFE version (for <script> tag usage)
              ${pkgs.esbuild}/bin/esbuild packages/measurement/snippet.ts \
                --bundle \
                --format=iife \
                --global-name=pSEO \
                --target=es2020 \
                --minify \
                --outfile=dist/measurement/snippet.iife.js

              echo "Build completed:"
              echo "  dist/measurement/snippet.esm.js ($(wc -c < dist/measurement/snippet.esm.js) bytes)"
              echo "  dist/measurement/snippet.iife.js ($(wc -c < dist/measurement/snippet.iife.js) bytes)"

              # Verify files exist
              if [ ! -f dist/measurement/snippet.esm.js ] || [ ! -f dist/measurement/snippet.iife.js ]; then
                echo "Build verification failed - output files missing"
                exit 1
              fi

              # Check reasonable file sizes (not empty, not excessive)
              ESM_SIZE=$(wc -c < dist/measurement/snippet.esm.js)
              IIFE_SIZE=$(wc -c < dist/measurement/snippet.iife.js)

              if [ "$ESM_SIZE" -lt 100 ] || [ "$IIFE_SIZE" -lt 100 ]; then
                echo "Build verification failed - output files too small (likely empty)"
                exit 1
              fi

              if [ "$ESM_SIZE" -gt 100000 ] || [ "$IIFE_SIZE" -gt 100000 ]; then
                echo "Warning: Output files larger than expected (>100KB)"
              fi
            ''}";
          };

          serve-examples = {
            type = "app";
            program = "${pkgs.writeShellScript "serve-examples" ''
              echo "Starting local server for examples..."
              echo "Serving from current directory"
              echo "Open http://localhost:8080/examples/phase-1.0/"
              echo ""
              echo "Press Ctrl+C to stop"
              ${pkgs.miniserve}/bin/miniserve . --port 8080 --index index.html
            ''}";
          };
        };

        checks = {
          tscheck = pkgs.runCommand "typescript-check" {
            buildInputs = [ pkgs.nodePackages.typescript ];
          } ''
            cp -r ${./.} ./src
            cd src
            ${pkgs.nodePackages.typescript}/bin/tsc --noEmit
            touch $out
          '';

          build = pkgs.runCommand "build-check" {
            buildInputs = [ pkgs.esbuild ];
          } ''
            cp -r ${./.} ./src
            cd src
            mkdir -p dist/measurement

            # Build both targets
            ${pkgs.esbuild}/bin/esbuild packages/measurement/snippet.ts \
              --bundle --format=esm --target=es2020 --outfile=dist/measurement/snippet.esm.js
            ${pkgs.esbuild}/bin/esbuild packages/measurement/snippet.ts \
              --bundle --format=iife --global-name=pSEO --target=es2020 --minify --outfile=dist/measurement/snippet.iife.js

            # Verify both files exist and have reasonable size
            [ -f dist/measurement/snippet.esm.js ] || exit 1
            [ -f dist/measurement/snippet.iife.js ] || exit 1
            [ "$(wc -c < dist/measurement/snippet.esm.js)" -gt 100 ] || exit 1
            [ "$(wc -c < dist/measurement/snippet.iife.js)" -gt 100 ] || exit 1

            touch $out
          '';
        };
      }
    );
}