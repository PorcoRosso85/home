{
  description = "KuzuDB TypeScript/Deno persistence layer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    log_ts.url = "path:../../telemetry/log_ts";
  };

  outputs = { self, nixpkgs, flake-utils, log_ts }:
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