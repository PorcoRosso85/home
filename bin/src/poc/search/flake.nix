{
  description = "Requirement Search POC - VSS/FTS/Hybrid検索";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/poc/search";
        
        # 共通のpatchelf処理（KuzuDB用）
        patchKuzu = ''
          for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
            [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib"
          done
        '';
        
        # 共通の実行ラッパー
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          
          # Python仮想環境の確認
          if [ ! -d ".venv" ]; then
            echo "🔧 Creating virtual environment..."
            ${pkgs.uv}/bin/uv venv
          fi
          
          # 依存関係のインストール確認
          if [ ! -f ".venv/.deps_installed" ]; then
            echo "📦 Installing dependencies..."
            ${pkgs.uv}/bin/uv pip install -r requirements.txt
            touch .venv/.deps_installed
          fi
          
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
          
          shellHook = ''
            echo "🔍 Requirement Search POC Development Environment"
            echo "Commands:"
            echo "  nix run .#test-red    - Run TDD Red phase tests"
            echo "  nix run .#test        - Run all tests"
            echo "  nix run .#lint        - Run linter"
            echo "  nix run .#format      - Format code"
          '';
        };
        
        apps = {
          # TDD Red フェーズテスト
          test-red = {
            type = "app";
            program = "${mkRunner "test-red" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              export PYTHONPATH="${projectDir}:${projectDir}/../../"
              
              echo "🔴 Running TDD Red phase tests..."
              exec .venv/bin/python test_requirement_search_red.py
            ''}";
          };
          
          # 全テスト実行
          test = {
            type = "app";
            program = "${mkRunner "test" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              export PYTHONPATH="${projectDir}:${projectDir}/../../"
              
              echo "🧪 Running all tests..."
              exec .venv/bin/pytest "$@"
            ''}";
          };
          
          # 環境セットアップ
          setup = {
            type = "app";
            program = "${mkRunner "setup" ''
              echo "🚀 Setting up search POC environment..."
              
              # requirements.txt作成
              cat > requirements.txt <<EOF
kuzu>=0.0.12
sentence-transformers>=2.2.0
pytest>=7.0.0
EOF
              
              # 依存関係の再インストール
              rm -f .venv/.deps_installed
              ${pkgs.uv}/bin/uv pip install -r requirements.txt
              touch .venv/.deps_installed
              
              echo "✅ Environment setup complete!"
            ''}";
          };
          
          # Lintチェック
          lint = {
            type = "app";
            program = "${mkRunner "lint" ''
              echo "🔍 Running linter..."
              
              # pyproject.tomlがない場合は作成
              if [ ! -f "pyproject.toml" ]; then
                cp ../../requirement/graph/pyproject.toml .
              fi
              
              exec ${pkgs.ruff}/bin/ruff check . "$@"
            ''}";
          };
          
          # フォーマット
          format = {
            type = "app";
            program = "${mkRunner "format" ''
              echo "✨ Formatting code..."
              
              if [ ! -f "pyproject.toml" ]; then
                cp ../../requirement/graph/pyproject.toml .
              fi
              
              exec ${pkgs.ruff}/bin/ruff format . "$@"
            ''}";
          };
          
          # VSS単体テスト
          test-vss = {
            type = "app";
            program = "${mkRunner "test-vss" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              export PYTHONPATH="${projectDir}:${projectDir}/../../"
              
              echo "🔍 Testing VSS module..."
              exec .venv/bin/pytest vss/ -v
            ''}";
          };
          
          # FTS単体テスト
          test-fts = {
            type = "app";
            program = "${mkRunner "test-fts" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              export PYTHONPATH="${projectDir}:${projectDir}/../../"
              
              echo "📝 Testing FTS module..."
              exec .venv/bin/pytest fts/ -v
            ''}";
          };
          
          # Hybrid単体テスト
          test-hybrid = {
            type = "app";
            program = "${mkRunner "test-hybrid" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              export PYTHONPATH="${projectDir}:${projectDir}/../../"
              
              echo "🔀 Testing Hybrid module..."
              exec .venv/bin/pytest hybrid/ -v
            ''}";
          };
        };
      });
}