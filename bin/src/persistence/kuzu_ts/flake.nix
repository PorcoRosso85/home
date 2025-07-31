{
  description = "KuzuDB TypeScript/Deno persistence layer with buildNpmPackage";

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
            stdenv.cc.cc.lib
            gcc
            patchelf
          ];
          
          shellHook = ''
            echo "KuzuDB TypeScript/Deno persistence layer"
            echo "Deno version: $(deno --version | head -n1)"
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
        
        # buildNpmPackageを使用したパッケージ定義
        # Default package (classic implementation)
        packages.default = pkgs.buildNpmPackage rec {
          pname = "kuzu_ts";
          version = "0.1.0";
          
          src = ./.;
          
          # package-lock.jsonのハッシュ
          npmDepsHash = "sha256-eSa6agcAMBrN8aOEDsCMUNYfd73L4nYjseETXedz1AQ=";
          
          buildInputs = with pkgs; [
            deno
            stdenv.cc.cc.lib
            patchelf
          ];
          
          # Skip npm build since this is a Deno project
          dontNpmBuild = true;
          
          # npm install後の処理
          postInstall = ''
            # Install Deno dependencies
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Set up deps directory
            mkdir -p $out/lib/kuzu_ts/deps
            ln -sf ${log_ts.lib.importPath} $out/lib/kuzu_ts/deps/log_ts
            
            # Copy Deno files
            mkdir -p $out/lib/kuzu_ts
            cp -r shared worker classic $out/lib/kuzu_ts/
            [ -d tests ] && cp -r tests $out/lib/kuzu_ts/
            [ -d examples ] && cp -r examples $out/lib/kuzu_ts/
            [ -d wasm ] && cp -r wasm $out/lib/kuzu_ts/
            cp mod.ts deno.json deno.lock package.json package-lock.json $out/lib/kuzu_ts/
            
            # Patch native modules
            if [ -d "$out/lib/node_modules/kuzu" ]; then
              for lib in $out/lib/node_modules/kuzu/*.node; do
                if [ -f "$lib" ]; then
                  ${pkgs.patchelf}/bin/patchelf \
                    --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" \
                    "$lib" || true
                fi
              done
            fi
            
            # Also patch modules in .deno cache if they exist
            if [ -d "$out/lib/node_modules/.deno" ]; then
              for lib in $out/lib/node_modules/.deno/*/node_modules/kuzu/*.node; do
                if [ -f "$lib" ]; then
                  ${pkgs.patchelf}/bin/patchelf \
                    --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" \
                    "$lib" || true
                fi
              done
            fi
            
            # Create wrapper script
            mkdir -p $out/bin
            cat > $out/bin/kuzu_ts <<EOF
            #!/bin/sh
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}:\$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="$out/lib/kuzu_ts"
            cd $out/lib/kuzu_ts
            exec ${pkgs.deno}/bin/deno run --allow-all --unstable-ffi "$out/lib/kuzu_ts/mod.ts" "\$@"
            EOF
            chmod +x $out/bin/kuzu_ts
          '';
          
          meta = with pkgs.lib; {
            description = "KuzuDB TypeScript/Deno persistence layer";
            homepage = "https://github.com/nixos/bin/src/persistence/kuzu_ts";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };
        
        # Classic implementation package (alias to default)
        packages.classic = self.packages.${system}.default;
        
        # Worker implementation package
        packages.worker = pkgs.buildNpmPackage rec {
          pname = "kuzu_ts_worker";
          version = "0.1.0";
          
          src = ./.;
          
          # package-lock.jsonのハッシュ
          npmDepsHash = "sha256-eSa6agcAMBrN8aOEDsCMUNYfd73L4nYjseETXedz1AQ=";
          
          buildInputs = with pkgs; [
            deno
            stdenv.cc.cc.lib
            patchelf
          ];
          
          # Skip npm build since this is a Deno project
          dontNpmBuild = true;
          
          # npm install後の処理
          postInstall = ''
            # Install Deno dependencies
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Set up deps directory
            mkdir -p $out/lib/kuzu_ts_worker/deps
            ln -sf ${log_ts.lib.importPath} $out/lib/kuzu_ts_worker/deps/log_ts
            
            # Copy Deno files
            mkdir -p $out/lib/kuzu_ts_worker
            cp -r shared worker $out/lib/kuzu_ts_worker/
            cp deno.json deno.lock package.json package-lock.json $out/lib/kuzu_ts_worker/
            
            # Create worker-specific mod.ts
            cat > $out/lib/kuzu_ts_worker/mod.ts <<'EOF'
            // Worker-specific entry point
            export * from "./shared/mod.ts";
            export * from "./worker/mod.ts";
            EOF
            
            # Patch native modules
            if [ -d "$out/lib/node_modules/kuzu" ]; then
              for lib in $out/lib/node_modules/kuzu/*.node; do
                if [ -f "$lib" ]; then
                  ${pkgs.patchelf}/bin/patchelf \
                    --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" \
                    "$lib" || true
                fi
              done
            fi
            
            # Create wrapper script
            mkdir -p $out/bin
            cat > $out/bin/kuzu_ts_worker <<EOF
            #!/bin/sh
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}:\$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="$out/lib/kuzu_ts_worker"
            cd $out/lib/kuzu_ts_worker
            exec ${pkgs.deno}/bin/deno run --allow-all --unstable-ffi --unstable-worker-options "$out/lib/kuzu_ts_worker/mod.ts" "\$@"
            EOF
            chmod +x $out/bin/kuzu_ts_worker
          '';
          
          meta = with pkgs.lib; {
            description = "KuzuDB TypeScript/Deno persistence layer - Worker implementation";
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
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            ${pkgs.deno}/bin/deno test tests/*.test.ts --allow-all --unstable-worker-options
          ''}/bin/test";
        };
      });
}