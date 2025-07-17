{
  description = "KuzuDB TypeScript/Deno persistence layer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
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
          ];
          
          shellHook = ''
            echo "KuzuDB TypeScript/Deno persistence layer"
            echo "Deno version: $(deno --version | head -n1)"
            # Set library path for native modules
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
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
            
            # Install dependencies
            ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
            
            # Run tests
            ${pkgs.deno}/bin/deno test --allow-read --allow-write --allow-net --allow-env --allow-ffi --unstable-ffi
            
            # Cleanup
            rm -rf $TEMP_DIR
          ''}/bin/test";
        };
      });
}