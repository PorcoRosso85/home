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
            nodePackages.ts-node
            esbuild
            miniserve # For serve-examples
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
            echo "Phase 1.1 SEO Tools:"
            echo "  nix run .#build-sitemap  - Build SEO sitemap.xml"
            echo "  nix run .#build-hreflang - Build multilingual hreflang tags"
            echo ""
            echo "Validation checks:"
            echo "  nix flake check         - Run all validation checks"
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

          build-sitemap = {
            type = "app";
            program = "${pkgs.writeShellScript "build-sitemap" ''
              echo "Building SEO sitemap..."

              # Ensure Node.js environment
              export PATH="${pkgs.nodejs_22}/bin:$PATH"

              # Compile and run TypeScript script
              ${pkgs.nodePackages.typescript}/bin/tsc scripts/build-sitemap.ts --outDir dist/scripts --target es2020 --module commonjs

              if [ $? -ne 0 ]; then
                echo "TypeScript compilation failed"
                exit 1
              fi

              # Run the compiled script
              ${pkgs.nodejs_22}/bin/node dist/scripts/build-sitemap.js

              if [ $? -eq 0 ]; then
                echo "Sitemap build completed successfully"
              else
                echo "Sitemap build failed"
                exit 1
              fi
            ''}";
          };

          build-hreflang = {
            type = "app";
            program = "${pkgs.writeShellScript "build-hreflang" ''
              echo "Building multilingual hreflang tags..."

              # Ensure Node.js environment
              export PATH="${pkgs.nodejs_22}/bin:${pkgs.nodePackages.ts-node}/bin:$PATH"

              # Run TypeScript directly with ts-node (skipping type checks for now)
              ${pkgs.nodePackages.ts-node}/bin/ts-node --transpile-only scripts/build-hreflang.ts

              if [ $? -eq 0 ]; then
                echo "Hreflang build completed successfully"
              else
                echo "Hreflang build failed"
                exit 1
              fi
            ''}";
          };
        };

        checks = {
          tscheck = pkgs.runCommand "typescript-check"
            {
              buildInputs = [ pkgs.nodePackages.typescript ];
            } ''
            cp -r ${./.} ./src
            cd src
            ${pkgs.nodePackages.typescript}/bin/tsc --noEmit
            touch $out
          '';

          build = pkgs.runCommand "build-check"
            {
              buildInputs = [ pkgs.esbuild ];
            } ''
            cp -r ${./.} ./src
            cd src
            # Make files writable and remove/recreate dist to avoid permission issues
            chmod -R u+w .
            rm -rf dist
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

          sitemap-exists = pkgs.runCommand "sitemap-exists-check"
            { } ''
            if [ -f ${./.}/public/sitemap.xml ]; then
              echo "✓ Sitemap file exists: public/sitemap.xml"
              touch $out
            else
              echo "❌ Sitemap file missing: public/sitemap.xml"
              echo "Run 'nix run .#build-sitemap' to generate sitemap"
              exit 1
            fi
          '';

          sitemap-validation = pkgs.runCommand "sitemap-validation-check"
            {
              buildInputs = [ pkgs.nodejs_22 ];
            } ''
            cp -r ${./.} ./src
            cd src

            if [ ! -f public/sitemap.xml ]; then
              echo "❌ Sitemap file missing for validation"
              exit 1
            fi

            # Run sitemap validation script
            ${pkgs.nodejs_22}/bin/node scripts/validate-sitemap.js public/sitemap.xml

            if [ $? -eq 0 ]; then
              echo "✓ Sitemap validation passed"
              touch $out
            else
              echo "❌ Sitemap validation failed"
              exit 1
            fi
          '';

          hreflang-validation = pkgs.runCommand "hreflang-validation-check"
            {
              buildInputs = [ pkgs.nodejs_22 ];
            } ''
            cp -r ${./.} ./src
            cd src

            # Check for hreflang files (HTML, JSON, or XML)
            HREFLANG_FILE=""
            if [ -f public/hreflang.html ]; then
              HREFLANG_FILE="public/hreflang.html"
            elif [ -f public/hreflang.json ]; then
              HREFLANG_FILE="public/hreflang.json"
            elif [ -f public/hreflang.xml ]; then
              HREFLANG_FILE="public/hreflang.xml"
            else
              echo "❌ No hreflang files found in public/"
              echo "Run 'nix run .#build-hreflang' to generate hreflang files"
              exit 1
            fi

            # Run hreflang validation script
            ${pkgs.nodejs_22}/bin/node scripts/validate-hreflang.js "$HREFLANG_FILE"

            if [ $? -eq 0 ]; then
              echo "✓ Hreflang validation passed"
              touch $out
            else
              echo "❌ Hreflang validation failed"
              exit 1
            fi
          '';

          phase-guard = pkgs.runCommand "phase-guard-check"
            {
              buildInputs = [ pkgs.nodejs_22 ];
            } ''
            cp -r ${./.} ./src
            cd src

            # Run phase guard validation
            ${pkgs.nodejs_22}/bin/node scripts/validate-phase-guard.js .

            if [ $? -eq 0 ]; then
              echo "✓ Phase guard validation passed"
              touch $out
            else
              echo "❌ Phase guard validation failed"
              exit 1
            fi
          '';
        };
      }
    );
}
