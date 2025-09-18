{
  description = "KuzuDB TypeScript/Deno persistence layer with FOD";

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
        
        # npm dependencies as Fixed Output Derivation
        npmDeps = pkgs.stdenv.mkDerivation {
          name = "kuzu-ts-npm-deps";
          src = ./.;
          
          buildInputs = with pkgs; [ deno ];
          
          # Fixed Output Derivation設定
          outputHashMode = "recursive";
          outputHashAlgo = "sha256";
          outputHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # 初回は失敗させて正しいハッシュを取得
          
          buildPhase = ''
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            
            # Install npm dependencies
            deno cache --node-modules-dir=node_modules --reload mod.ts
          '';
          
          installPhase = ''
            mkdir -p $out
            cp -r node_modules $out/
          '';
        };
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
        
        # パッケージ定義（node_modules込み）
        packages.default = pkgs.stdenv.mkDerivation rec {
          pname = "kuzu_ts";
          version = "0.1.0";
          
          src = ./.;
          
          buildInputs = with pkgs; [
            deno
            nodejs_20
            stdenv.cc.cc.lib
            patchelf
          ];
          
          buildPhase = ''
            runHook preBuild
            
            # Set up environment
            export HOME=$TMPDIR
            export DENO_DIR=$TMPDIR/.deno
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Copy source files
            cp -r $src/* .
            chmod -R u+w .
            
            # Use pre-cached npm dependencies
            ln -s ${npmDeps}/node_modules node_modules
            
            # Set up deps directory
            rm -rf deps/log_ts
            mkdir -p deps
            ln -sf ${log_ts.lib.importPath} deps/log_ts
            
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
          
          installPhase = ''
            runHook preInstall
            
            # Create output directory
            mkdir -p $out/lib
            
            # Copy all source files to lib directory
            cp -r core shared worker tests examples $out/lib/
            cp mod.ts deno.json deno.lock $out/lib/
            
            # Copy node_modules
            cp -r node_modules $out/lib/
            
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
                "./worker": "./worker/mod.ts"
              }
            }
            EOF
            
            runHook postInstall
          '';
          
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
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            ${pkgs.deno}/bin/deno test tests/*.test.ts --allow-all --unstable-worker-options
          ''}/bin/test";
        };
      });
}