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
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pytest
          kuzu
        ]);
        
      in {
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
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
              cd ${self}
              exec ${pythonEnv}/bin/python run.py "$@"
            ''}";
          };
          
          # テスト
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}"
              export RGL_DB_PATH="/tmp/test_rgl_db"
              export RGL_SKIP_SCHEMA_CHECK="true"
              
              # 実際のプロジェクトディレクトリを使用
              PROJECT_DIR="/home/nixos/bin/src/requirement/graph"
              if [ -f "$PROJECT_DIR/.venv/bin/pytest" ]; then
                cd "$PROJECT_DIR"
                exec "$PROJECT_DIR/.venv/bin/pytest" "$@"
              else
                echo "Error: $PROJECT_DIR/.venv/bin/pytest not found. Run 'uv sync' first."
                exit 1
              fi
            ''}";
          };
          
          # スキーマ適用
          schema = {
            type = "app";
            program = "${pkgs.writeShellScript "schema" ''
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}"
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              cd ${self}
              echo '{"type": "schema", "action": "apply", "create_test_data": true}' | ${pythonEnv}/bin/python run.py
            ''}";
          };
        };
      });
}