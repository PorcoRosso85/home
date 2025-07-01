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
        
        # Python環境（kuzuを含む）
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pytest
          kuzu
          # その他の依存関係はuv.lockから
        ]);
        
      in {
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            uv
          ];
          
          shellHook = ''
            echo "RGL Development Environment"
            export RGL_DB_PATH="./rgl_db"
            echo "RGL_DB_PATH: $RGL_DB_PATH"
          '';
        };
        
        # アプリケーション
        apps = {
          # メインアプリケーション
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "rgl" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec ${pkgs.uv}/bin/uv run python -m requirement.graph.main "$@"
            ''}";
          };
          
          # テスト実行（uvを使用）
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export RGL_DB_PATH="/tmp/test_rgl_db"
              export RGL_SKIP_SCHEMA_CHECK="true"
              exec ${pkgs.uv}/bin/uv run pytest "$@"
            ''}";
          };
          
          # テスト実行（純粋なpythonEnv使用）
          test-nix = {
            type = "app";
            program = "${pkgs.writeShellScript "test-nix" ''
              export RGL_DB_PATH="/tmp/test_rgl_db"
              export RGL_SKIP_SCHEMA_CHECK="true"
              cd ${./.}
              exec ${pythonEnv}/bin/pytest "$@"
            ''}";
          };
          
          # スキーマ適用
          apply-schema = {
            type = "app";
            program = "${pkgs.writeShellScript "apply-schema" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec ${pkgs.uv}/bin/uv run python -m requirement.graph.infrastructure.apply_ddl_schema "$@"
            ''}";
          };
        };
      });
}