{
  description = "Requirement Graph Logic (RGL) - 要件管理システム";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-py.url = "path:../../persistence/kuzu_py";
    python-flake.url = "path:../../flakes/python";
    vss-kuzu.url = "path:../../search/vss_kuzu";
    fts-kuzu.url = "path:../../search/fts_kuzu";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-py, python-flake, vss-kuzu, fts-kuzu, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/requirement/graph";
        
        
        # VSS/FTSパッケージの取得（flake経由）
        vssKuzuPkg = vss-kuzu.packages.${system}.vssKuzu;
        ftsKuzuPkg = fts-kuzu.packages.${system}.default;  # FTSパッケージを有効化
        
        # Python環境 - 開発環境用
        pythonEnv = pkgs.python312.withPackages (ps: [
          # 親flakeの基本パッケージ
          ps.pytest
          # kuzu本体
          ps.kuzu
          # VSS/FTSパッケージ（flake経由）
          vssKuzuPkg
          ftsKuzuPkg
          # 追加の依存関係
          ps.numpy
          ps.sentence-transformers
          ps.torch
          ps.scipy
          ps.sentencepiece
          # 開発ツール
          ps.pytest-xdist
          ps.hypothesis
        ]);
        
        # 共通の実行ラッパー
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          ${script}
        '';
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            ruff
          ];
          
          shellHook = ''
            echo "Requirement Graph Logic (RGL) Development Environment"
            echo "Environment ready!"
          '';
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
              exec ${pythonEnv}/bin/pytest "$@"
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
              echo '{"type": "schema", "action": "apply", "create_test_data": true}' | ${pythonEnv}/bin/python main.py
              
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
          
          test-help = {
            type = "app";
            program = "${pkgs.writeShellScript "test-help" ''
              cat << 'EOF'
📊 Test Runner Commands

基本コマンド:
  nix run .#test                    # 通常のテスト実行
  nix run .#test-timed              # 実行時間付きテスト
  nix run .#test-fast               # 高速テストのみ（@pytest.mark.slowを除外）

DuckDBへの永続化:
  # テスト結果をDuckDBに保存（堅牢な行単位インポート）
  nix run .#test-timed 2>&1 | nix run nixpkgs#duckdb -- test.db -c "
    CREATE OR REPLACE TABLE raw_output (line_text VARCHAR);
    INSERT INTO raw_output 
    SELECT * FROM read_csv('/dev/stdin', columns={'line_text': 'VARCHAR'}, auto_detect=false);
  "

  # より詳細な構造化データ保存
  nix run .#test-timed 2>&1 | duckdb test.db -c "
    CREATE TABLE IF NOT EXISTS test_output (
      session_id UUID DEFAULT gen_random_uuid(),
      line_no BIGINT,
      line_text VARCHAR,
      inserted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO test_output (line_no, line_text)
    SELECT ROW_NUMBER() OVER (), column0
    FROM read_csv('/dev/stdin', delim='\n', header=false);
  "

分析の実行:
  # 保存したデータを分析
  duckdb test.db < analysis/slow_tests.sql
  duckdb test.db < analysis/test_durations.sql

使用例:
  # 特定のテストを計測付きで実行
  nix run .#test-timed -- tests/test_foo.py

  # 特定のテストパターンのみ実行
  nix run .#test-timed -- -k "test_requirement"

  # 実行時間を永続化して分析
  nix run .#test-timed 2>&1 | duckdb results.db -c "..."
  duckdb results.db -c "SELECT * FROM raw_output WHERE column0 LIKE '%slowest durations%' LIMIT 10"

マーキング:
  # テストに@pytest.mark.slowを付けることで、test-fastから除外可能
  @pytest.mark.slow
  def test_heavy_computation():
      ...

詳細は analysis/README.md を参照
EOF
            ''}";
          };
          
          test-timed = {
            type = "app";
            program = "${mkRunner "test-timed" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              echo "⏱️  Running tests with timing information..."
              exec ${pythonEnv}/bin/pytest --durations=0 "$@"
            ''}";
          };
          
          test-fast = {
            type = "app";
            program = "${mkRunner "test-fast" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              echo "🚀 Running fast tests only (excluding @pytest.mark.slow)..."
              exec ${pythonEnv}/bin/pytest -m "not slow" "$@"
            ''}";
          };
          
          test-with-db = {
            type = "app";
            program = "${mkRunner "test-with-db" ''
              echo "⚠️  'nix run .#test-with-db' は非推奨です。"
              echo ""
              echo "新しい方法を使用してください:"
              echo "  nix run .#test-timed              # 実行時間付きテスト"
              echo "  nix run .#test-help               # 詳細なヘルプを表示"
              echo ""
              echo "DuckDBへの永続化:"
              echo "  nix run .#test-timed 2>&1 | duckdb test.db -c \"CREATE TABLE raw_output AS SELECT * FROM read_csv('/dev/stdin', delim='\\n', header=false);\""
              echo ""
              exit 1
            ''}";
          };
          
          run = {
            type = "app";
            program = "${mkRunner "run" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec ${pythonEnv}/bin/python -m requirement.graph "$@"
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
              echo '{"type": "init", "action": "apply", "create_test_data": true}' | ${pythonEnv}/bin/python -m requirement.graph
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
              exec ${pkgs.ruff}/bin/ruff check . "$@"
            ''}";
          };
          
          "lint.fix" = {
            type = "app";
            program = "${mkRunner "lint-fix" ''
              echo "🔧 Running linter with auto-fix..."
              exec ${pkgs.ruff}/bin/ruff check --fix . "$@"
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