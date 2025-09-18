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
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ deno2nix.overlays.default ];
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
            echo "KuzuDB TypeScript/Deno persistence layer with deno2nix"
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
        
        # deno2nixを使用したパッケージ定義
        packages.default = pkgs.deno2nix.mkExecutable {
          pname = "kuzu_ts";
          version = "0.1.0";
          
          src = ./.;
          bin = "kuzu_ts";
          entrypoint = "mod.ts";
          lockfile = "deno.lock";
          config = "deno.json";
          
          allow = {
            all = true;
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