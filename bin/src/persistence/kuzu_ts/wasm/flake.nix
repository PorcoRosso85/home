{
  description = "KuzuDB TypeScript/Deno WASM implementation";

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
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            wasm-pack
            wasm-bindgen-cli
          ];
          
          shellHook = ''
            echo "KuzuDB WASM TypeScript/Deno implementation"
            echo "Deno version: $(deno --version | head -n1)"
            echo ""
            echo "WASM build tools available:"
            echo "- wasm-pack: $(wasm-pack --version)"
            echo "- wasm-bindgen: $(wasm-bindgen --version)"
          '';
        };
        
        # WASM package definition (placeholder for future implementation)
        packages.default = pkgs.buildNpmPackage rec {
          pname = "kuzu_ts_wasm";
          version = "0.1.0";
          
          src = ./.;
          
          # This will need to be updated when package-lock.json is created
          npmDepsHash = pkgs.lib.fakeSha256;
          
          buildInputs = with pkgs; [
            deno
            nodejs_20
            wasm-pack
          ];
          
          # WASM-specific build configuration
          npmBuildScript = "build:wasm";
          
          # Install phase for WASM
          postInstall = ''
            # Install Deno dependencies
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            
            # Copy WASM files
            mkdir -p $out/lib/kuzu_ts_wasm
            cp -r wasm pkg $out/lib/kuzu_ts_wasm/ 2>/dev/null || true
            cp package.json package-lock.json $out/lib/kuzu_ts_wasm/
            
            # Create WASM-specific mod.ts if it doesn't exist
            if [ ! -f "$out/lib/kuzu_ts_wasm/mod.ts" ]; then
              cat > $out/lib/kuzu_ts_wasm/mod.ts <<'EOF'
            // WASM-specific entry point
            export * from "./wasm/mod.ts";
            EOF
            fi
            
            # Create wrapper script
            mkdir -p $out/bin
            cat > $out/bin/kuzu_ts_wasm <<EOF
            #!/bin/sh
            export KUZU_TS_WASM_PATH="$out/lib/kuzu_ts_wasm"
            cd $out/lib/kuzu_ts_wasm
            exec ${pkgs.deno}/bin/deno run --allow-all "$out/lib/kuzu_ts_wasm/mod.ts" "\$@"
            EOF
            chmod +x $out/bin/kuzu_ts_wasm
          '';
          
          meta = with pkgs.lib; {
            description = "KuzuDB TypeScript/Deno persistence layer - WASM implementation";
            homepage = "https://github.com/nixos/bin/src/persistence/kuzu_ts";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.all; # WASM can run on all platforms
          };
        };
        
        # WASM-specific test runner
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test-wasm" ''
            echo "Running WASM tests..."
            ${pkgs.deno}/bin/deno test tests/*.test.ts --allow-all
          ''}/bin/test-wasm";
        };
      });
}