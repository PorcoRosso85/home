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
            ruff
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
              export RGL_SKIP_SCHEMA_CHECK="true"
              exec .venv/bin/pytest "$@"
            ''}";
          };
          
          "test.up" = {
            type = "app";
            program = "${mkRunner "test-up" ''
              echo "🚀 Setting up test environment..."
              
              # テスト用DBディレクトリの作成
              export RGL_DB_PATH="/tmp/test_rgl_db"
              mkdir -p "$RGL_DB_PATH"
              
              # 既存のテストDBをバックアップ（存在する場合）
              if [ -d "$RGL_DB_PATH" ] && [ "$(ls -A $RGL_DB_PATH 2>/dev/null)" ]; then
                echo "📦 Backing up existing test database..."
                rm -rf "$RGL_DB_PATH.bak"
                mv "$RGL_DB_PATH" "$RGL_DB_PATH.bak"
                mkdir -p "$RGL_DB_PATH"
              fi
              
              # テスト用スキーマの適用
              echo "📊 Applying test schema..."
              export RGL_SKIP_SCHEMA_CHECK="true"
              echo '{"type": "schema", "action": "apply", "create_test_data": true}' | .venv/bin/python run.py
              
              echo "✅ Test environment is ready!"
              echo "   DB Path: $RGL_DB_PATH"
            ''}";
          };
          
          "test.down" = {
            type = "app";
            program = "${mkRunner "test-down" ''
              echo "🧹 Cleaning up test environment..."
              
              export RGL_DB_PATH="/tmp/test_rgl_db"
              
              # テストDBの削除
              if [ -d "$RGL_DB_PATH" ]; then
                echo "🗑️  Removing test database at $RGL_DB_PATH..."
                rm -rf "$RGL_DB_PATH"
              fi
              
              # バックアップの復元（オプション）
              if [ -d "$RGL_DB_PATH.bak" ]; then
                echo "♻️  Found backup database"
                read -p "Restore backup? (y/N) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                  mv "$RGL_DB_PATH.bak" "$RGL_DB_PATH"
                  echo "✅ Backup restored"
                else
                  rm -rf "$RGL_DB_PATH.bak"
                  echo "🗑️  Backup removed"
                fi
              fi
              
              # その他のテスト成果物のクリーンアップ
              echo "🧹 Cleaning up test artifacts..."
              find . -name "*.pyc" -delete
              find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
              find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
              
              echo "✅ Test environment cleaned up!"
            ''}";
          };
          
          run = {
            type = "app";
            program = "${mkRunner "run" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec .venv/bin/python run.py "$@"
            ''}";
          };
          
          init = {
            type = "app";
            program = "${mkRunner "init" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              
              # スキーマ状態確認
              if [ -d "$RGL_DB_PATH" ] && [ -f "$RGL_DB_PATH/catalog.kz" ]; then
                echo "ℹ️  データベースは既に存在します: $RGL_DB_PATH"
                echo "再初期化する場合は、データベースディレクトリを削除してから実行してください"
                echo "  rm -rf $RGL_DB_PATH"
                exit 0
              fi
              
              # 初期化実行
              echo '{"type": "init", "action": "apply", "create_test_data": true}' | .venv/bin/python run.py
            ''}";
          };
          
          # 互換性のため旧名称も維持
          schema = {
            type = "app";
            program = "${mkRunner "schema" ''
              echo "⚠️  'nix run .#schema' は非推奨です。'nix run .#init' を使用してください"
              exec nix run .#init -- "$@"
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${mkRunner "lint" ''
              echo "🔍 Running linter (ruff)..."
              
              # ruffがvenv内にある場合は使用、なければシステムのruffを使用
              if [ -f ".venv/bin/ruff" ]; then
                exec .venv/bin/ruff check . "$@"
              else
                exec ${pkgs.ruff}/bin/ruff check . "$@"
              fi
            ''}";
          };
          
          "lint.fix" = {
            type = "app";
            program = "${mkRunner "lint-fix" ''
              echo "🔧 Running linter with auto-fix..."
              
              if [ -f ".venv/bin/ruff" ]; then
                exec .venv/bin/ruff check --fix . "$@"
              else
                exec ${pkgs.ruff}/bin/ruff check --fix . "$@"
              fi
            ''}";
          };
          
          "lint.fix-unsafe" = {
            type = "app";
            program = "${mkRunner "lint-fix-unsafe" ''
              echo "⚠️  Running linter with unsafe fixes..."
              echo "This may change code behavior. Review changes carefully!"
              
              if [ -f ".venv/bin/ruff" ]; then
                exec .venv/bin/ruff check --fix --unsafe-fixes . "$@"
              else
                exec ${pkgs.ruff}/bin/ruff check --fix --unsafe-fixes . "$@"
              fi
            ''}";
          };
          
          "lint.preview" = {
            type = "app";
            program = "${mkRunner "lint-preview" ''
              echo "👀 Previewing fixes (no changes will be made)..."
              
              if [ -f ".venv/bin/ruff" ]; then
                exec .venv/bin/ruff check --fix --diff . "$@"
              else
                exec ${pkgs.ruff}/bin/ruff check --fix --diff . "$@"
              fi
            ''}";
          };
          
          "lint.stats" = {
            type = "app";
            program = "${mkRunner "lint-stats" ''
              echo "📊 Lint statistics..."
              
              if [ -f ".venv/bin/ruff" ]; then
                .venv/bin/ruff check --statistics . "$@" | sort -k1 -n -r
              else
                ${pkgs.ruff}/bin/ruff check --statistics . "$@" | sort -k1 -n -r
              fi
            ''}";
          };
          
          format = {
            type = "app";
            program = "${mkRunner "format" ''
              echo "✨ Formatting code..."
              
              if [ -f ".venv/bin/ruff" ]; then
                exec .venv/bin/ruff format . "$@"
              else
                exec ${pkgs.ruff}/bin/ruff format . "$@"
              fi
            ''}";
          };
        };
      });
}