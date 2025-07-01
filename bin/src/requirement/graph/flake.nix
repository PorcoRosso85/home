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
        
      in {
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            uv
            gcc
          ];
          
          # C++ライブラリへのパスを提供
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
          ];
          
          shellHook = ''
            echo "RGL Development Environment"
            export RGL_DB_PATH="./rgl_db"
            echo "RGL_DB_PATH: $RGL_DB_PATH"
            echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
            
            # uvの仮想環境をアクティベート（存在する場合）
            if [ -f .venv/bin/activate ]; then
              source .venv/bin/activate
            fi
          '';
        };
        
        # アプリケーション
        apps = {
          # 実装（メインアプリケーション）
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "rgl" ''
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}"
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec ${pkgs.uv}/bin/uv run python run.py "$@"
            ''}";
          };
          
          # テスト
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}"
              export RGL_DB_PATH="/tmp/test_rgl_db"
              export RGL_SKIP_SCHEMA_CHECK="true"
              exec ${pkgs.uv}/bin/uv run pytest "$@"
            ''}";
          };
        };
      });
}