{
  description = "KuzuDB TypeScript/Deno persistence layer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    log_ts.url = "path:../../telemetry/log_ts";
    deno2nix.url = "github:SnO2WMaN/deno2nix";
  };

  outputs = { self, nixpkgs, flake-utils, log_ts, deno2nix }:
    {
      # システム非依存の出力
      lib = {
        importPath = ./.;
        moduleUrl = "file://${./.}/mod.ts";
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            # C++ dependencies for kuzu native module
            stdenv.cc.cc.lib
            gcc
            patchelf  # For fixing native module paths
          ];
          
          shellHook = ''
            echo "KuzuDB TypeScript/Deno persistence layer"
            echo "Deno version: $(deno --version | head -n1)"
            # Set library path for native modules
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Link log_ts for development
            mkdir -p deps
            ln -sf ${log_ts.lib.importPath} deps/log_ts
            
            # Patch KuzuDB native modules if they exist
            if [ -d "node_modules/.deno" ]; then
              for lib in node_modules/.deno/*/node_modules/kuzu/*.node; do
                [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib" || true
              done
            fi
          '';
        };
        
        # deno2nixを使用したパッケージ定義
        packages.default = deno2nix.packages.${system}.mkDenoDerivation rec {
          pname = "kuzu_ts";
          version = "0.1.0";
          
          src = ./.;
          
          buildInputs = with pkgs; [
            deno
            nodejs_20
            stdenv.cc.cc.lib
            patchelf
          ];
          
          # Build phase - install dependencies and patch native modules
          buildPhase = ''
            runHook preBuild
            
            echo "Starting build phase..."
            echo "Current directory: $(pwd)"
            echo "Source directory: $src"
            
            # Set up environment
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Copy source files to build directory where we have write permissions
            echo "Copying source files..."
            cp -r $src/* . || echo "Failed to copy source files"
            # Also copy hidden directories like node_modules
            cp -r $src/node_modules . 2>/dev/null || echo "No node_modules in source"
            chmod -R u+w . || echo "Failed to chmod"
            
            # Remove existing deps/log_ts and create fresh symlink
            echo "Setting up deps directory..."
            rm -rf deps/log_ts
            mkdir -p deps
            echo "Linking log_ts from ${log_ts.lib.importPath}..."
            ln -sf ${log_ts.lib.importPath} deps/log_ts
            
            # Skip npm install - use existing node_modules
            echo "Using existing node_modules (static approach)..."
            
            # Patch native modules for Nix compatibility
            if [ -d "node_modules/.deno" ]; then
              for lib in node_modules/.deno/*/node_modules/kuzu/*.node; do
                if [ -f "$lib" ]; then
                  ${pkgs.patchelf}/bin/patchelf \
                    --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" \
                    "$lib" || true
                fi
              done
            fi
            
            runHook postBuild
          '';
          
          # Install phase - copy all files and make it self-contained
          installPhase = ''
            runHook preInstall
            
            # Create output directory
            mkdir -p $out/lib
            
            # Copy all source files to lib directory
            cp -r core $out/lib/
            cp -r tests $out/lib/
            cp mod.ts mod_worker.ts version.ts deno.json deno.lock $out/lib/
            
            # Copy node_modules from current directory
            echo "Checking for node_modules..."
            if [ -d "${./node_modules}" ]; then
              echo "Copying node_modules from source directory..."
              cp -r ${./node_modules} $out/lib/node_modules
            elif [ -d "node_modules" ]; then
              echo "Copying node_modules from build directory..."
              cp -r node_modules $out/lib/
            else
              echo "WARNING: node_modules directory not found!"
            fi
            
            # Copy deps directory with log_ts link
            cp -r deps $out/lib/
            
            # Create a wrapper script for runtime usage
            mkdir -p $out/bin
            cat > $out/bin/kuzu_ts <<EOF
            #!/bin/sh
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}:\$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="$out/lib"
            exec ${pkgs.deno}/bin/deno run --allow-read --allow-write --allow-net --allow-env --allow-ffi --unstable-ffi "$out/lib/mod.ts" "\$@"
            EOF
            chmod +x $out/bin/kuzu_ts
            
            # Create package.json for npm compatibility
            cat > $out/lib/package.json <<EOF
            {
              "name": "kuzu_ts",
              "version": "${version}",
              "type": "module",
              "main": "mod.ts",
              "exports": {
                ".": "./mod.ts",
                "./worker": "./mod_worker.ts"
              }
            }
            EOF
            
            runHook postInstall
          '';
          
          # Metadata
          meta = with pkgs.lib; {
            description = "KuzuDB TypeScript/Deno persistence layer";
            homepage = "https://github.com/nixos/bin/src/persistence/kuzu_ts";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };
        
        # テストランナー
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            # Copy source to temp directory to avoid read-only issues
            TEMP_DIR=$(mktemp -d)
            cp -r ${./.}/* $TEMP_DIR/
            cd $TEMP_DIR
            
            # Set up environment
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export DENO_DIR="$TEMP_DIR/.deno"
            
            # Link log_ts dependency
            mkdir -p $TEMP_DIR/deps
            ln -s ${log_ts.lib.importPath} $TEMP_DIR/deps/log_ts
            
            # Install dependencies
            ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
            
            # Patch native modules
            for lib in node_modules/.deno/*/node_modules/kuzu/*.node; do
              [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib" || true
            done
            
            # Debug: List test files
            echo "Looking for test files in: $TEMP_DIR/tests/"
            ls -la $TEMP_DIR/tests/*.test.ts || echo "No test files found"
            
            # Run all tests from current directory
            echo "Running all tests..."
            cd $TEMP_DIR
            ${pkgs.deno}/bin/deno test tests/*.test.ts --allow-read --allow-write --allow-net --allow-env --allow-ffi --unstable-ffi
            
            # Cleanup with proper permissions
            chmod -R u+w $TEMP_DIR || true
            rm -rf $TEMP_DIR
          ''}/bin/test";
        };
      });
}