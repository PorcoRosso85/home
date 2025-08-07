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
        
        # requirement-graph パッケージのビルド（src/requirement全体を使用）
        requirementSrc = pkgs.runCommand "requirement-src" {} ''
          mkdir -p $out/requirement/graph
          cp -r ${self} $out/requirement/graph
          # 親のrequirement/__init__.pyも作成
          echo "# requirement package" > $out/requirement/__init__.py
          # pyproject.tomlを最上位にコピー
          cp ${self}/pyproject.toml $out/
        '';
        
        requirementGraphPkg = pkgs.python312.pkgs.buildPythonPackage {
          pname = "requirement-graph";
          version = "0.1.0";
          src = requirementSrc;
          format = "pyproject";
          
          nativeBuildInputs = with pkgs.python312.pkgs; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312.pkgs; [
            kuzu
            vssKuzuPkg
            ftsKuzuPkg
          ];
          
          # テスト実行時の環境変数
          checkPhase = ''
            export RGL_SKIP_SCHEMA_CHECK="true"
          '';
          
          # テストは無効化（開発環境で実行）
          doCheck = false;
        };
        
        # Python環境 - 開発環境用
        pythonEnv = pkgs.python312.withPackages (ps: [
          # requirement-graph パッケージ
          requirementGraphPkg
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
          # JSON出力用
          ps.pytest-json-report
        ]);
        
        # 共通の実行ラッパー
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          export PYTHONPATH="/home/nixos/bin/src:${projectDir}/..:$PYTHONPATH"
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
            echo "Setting up PYTHONPATH for requirement.graph module..."
            export PYTHONPATH="/home/nixos/bin/src:${projectDir}/..:$PYTHONPATH"
            echo "PYTHONPATH set to: $PYTHONPATH"
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
          
          # テストコマンドは1つだけ
          test = {
            type = "app";
            program = "${mkRunner "test" ''
              export RGL_SKIP_SCHEMA_CHECK="true"
              exec ${pythonEnv}/bin/pytest "$@"
            ''}";
          };
          
          run = {
            type = "app";
            program = "${mkRunner "run" ''
              export RGL_DB_PATH="''${RGL_DB_PATH:-./rgl_db}"
              exec ${pythonEnv}/bin/python ${projectDir}/main.py "$@"
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
              echo '{"type": "init", "action": "apply", "create_test_data": true}' | ${pythonEnv}/bin/requirement-graph
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
              echo "🔍 Running linters..."
              ${pkgs.ruff}/bin/ruff check . || exit 1
              echo "✅ All checks passed!"
            ''}";
          };
          
          type-check = {
            type = "app";
            program = "${mkRunner "type-check" ''
              echo "🔍 Running type checks..."
              ${pythonEnv}/bin/python -m mypy . --ignore-missing-imports || exit 1
              echo "✅ Type checks passed!"
            ''}";
          };
        };
        
        packages = {
          default = requirementGraphPkg;
          
          # requirement-graph Python パッケージ
          requirementGraph = requirementGraphPkg;
          
          # Python環境を外部から利用可能にする
          pythonEnv = pythonEnv;
        };
      });
}