{
  description = "Requirement Search POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/poc/search";
        
        mkRunner = name: script: pkgs.writeShellScript name ''
          cd ${projectDir}
          [ ! -d ".venv" ] && ${pkgs.uv}/bin/uv venv
          [ ! -f ".venv/.deps_installed" ] && ${pkgs.uv}/bin/uv pip install pytest && touch .venv/.deps_installed
          
          for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
            [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib"
          done
          
          ${script}
        '';
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ python311 uv patchelf stdenv.cc.cc.lib ruff ];
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${projectDir}
              export PYTHONPATH="${projectDir}/../../"
              export RGL_SKIP_SCHEMA_CHECK="true"
              
              # 規約準拠: requirement/graphのvenvを使用
              VENV_PATH="/home/nixos/bin/src/requirement/graph/.venv"
              if [ ! -d "$VENV_PATH" ]; then
                echo "エラー: requirement/graphの仮想環境が見つかりません"
                echo "先にrequirement/graphでセットアップを実行してください"
                exit 1
              fi
              
              # 仕様テストを優先的に実行
              echo "=== Search POC テスト実行 ==="
              echo ""
              echo "1. 仕様テスト (Specification Tests)"
              $VENV_PATH/bin/python -m pytest test_search_poc_spec.py test_kuzu_native_spec.py -v
              
              echo ""
              echo "2. 統合テスト (Integration Tests)"
              $VENV_PATH/bin/python -m pytest test_kuzu_vss_fts_integration.py test_requirement_search_integration.py -v -x
              
              echo ""
              echo "3. E2Eテスト (End-to-End Tests)"
              $VENV_PATH/bin/python test_hybrid_search_e2e.py
              
              echo ""
              echo "4. その他のテスト"
              $VENV_PATH/bin/python -m pytest -v \
                --ignore=test_search_poc_spec.py \
                --ignore=test_kuzu_native_spec.py \
                --ignore=test_kuzu_vss_fts_integration.py \
                --ignore=test_requirement_search_integration.py \
                --ignore=test_hybrid_search_e2e.py
            ''}";
          };
          
          # 単体テスト実行用
          test-spec = {
            type = "app";
            program = "${pkgs.writeShellScript "test-spec" ''
              cd ${projectDir}
              export PYTHONPATH="${projectDir}/../../"
              echo "=== 仕様テストのみ実行 ==="
              exec /home/nixos/bin/src/requirement/graph/.venv/bin/python -m pytest test_search_poc_spec.py test_kuzu_native_spec.py -v
            ''}";
          };
          
          test-integration = {
            type = "app";
            program = "${pkgs.writeShellScript "test-integration" ''
              cd ${projectDir}
              export PYTHONPATH="${projectDir}/../../"
              export RGL_SKIP_SCHEMA_CHECK="true"
              echo "=== 統合テストのみ実行 ==="
              exec /home/nixos/bin/src/requirement/graph/.venv/bin/python -m pytest test_kuzu_vss_fts_integration.py test_requirement_search_integration.py -v -s
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${mkRunner "lint" ''
              exec ${pkgs.ruff}/bin/ruff check . "$@"
            ''}";
          };
          
          format = {
            type = "app";
            program = "${mkRunner "format" ''
              exec ${pkgs.ruff}/bin/ruff format . "$@"
            ''}";
          };
        };
      });
}