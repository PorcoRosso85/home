{
  description = "Requirement Graph Logic (RGL) - 要件管理システム";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/requirement/graph";
        
        # 共通のpatchelf処理
        patchKuzu = ''
          for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
            [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib"
          done
        '';
        
        # 共通の実行ラッパー
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          ${patchKuzu}
          ${script}
        '';
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            uv
            patchelf
            stdenv.cc.cc.lib
          ];
        };
        
        apps = {
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${self}/README.md || echo "README.md not found"
            ''}";
          };
          
          test = {
            type = "app";
            program = "${mkRunner "test" ''
              export RGL_DB_PATH="/tmp/test_rgl_db"
              export RGL_SKIP_SCHEMA_CHECK="true"
              exec .venv/bin/pytest "$@"
            ''}";
          };
          
          run = {
            type = "app";
            program = "${mkRunner "run" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec .venv/bin/python run.py "$@"
            ''}";
          };
          
          schema = {
            type = "app";
            program = "${mkRunner "schema" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              echo '{"type": "schema", "action": "apply", "create_test_data": true}' | .venv/bin/python run.py
            ''}";
          };
        };
      });
}