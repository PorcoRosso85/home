{
  description = "Unified Sync - KuzuDB WASM + WebSocket + Event Store";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pytest
          pytest-asyncio
          websockets
          httpx
        ]);
        
      in
      {
        # デフォルトアプリ（利用可能なコマンド一覧を表示）
        apps.default = {
          type = "app";
          program = let
            appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
            helpText = ''
              🔄 Unified Sync - KuzuDB同期実装
              
              利用可能なコマンド:
              ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
            '';
          in "${pkgs.writeShellScript "show-help" ''
            cat << 'EOF'
            ${helpText}
            EOF
          ''}";
        };
        
        # README表示アプリ
        apps.readme = {
          type = "app";
          program = "${pkgs.writeShellScript "show-readme" ''
            if [ -f README.md ]; then
              cat README.md
            else
              echo "README.md not found"
              exit 1
            fi
          ''}";
        };
        
        # テスト実行用アプリ（外部スクリプトを呼び出すだけ）
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            set -e
            
            echo "🔄 Starting Unified Sync Tests"
            echo "============================="
            
            # 環境変数を設定
            export DENO_PATH="${pkgs.deno}/bin/deno"
            export PATH="${pkgs.deno}/bin:${pythonEnv}/bin:$PATH"
            
            # ポート競合を避けるため、既存のプロセスをクリーンアップ
            echo "🧹 Cleaning up existing processes..."
            pkill -f "deno.*websocket-server" || true
            pkill -f "python.*e2e_test" || true
            sleep 1
            
            # テスト結果
            E2E_EXIT=0
            INTEGRATION_EXIT=0
            
            # E2Eテスト (Python pytest)
            echo ""
            echo "🐍 Running E2E tests with pytest..."
            ${pythonEnv}/bin/pytest ./tests/e2e_test.py -v || E2E_EXIT=$?
            
            # 統合テスト (TypeScript)
            echo ""
            echo "📦 Running integration tests with Deno..."
            ${pkgs.deno}/bin/deno test ./tests/integration.test.ts --no-check --allow-env --allow-net --allow-run || INTEGRATION_EXIT=$?
            
            # 再接続テスト (TypeScript)
            echo ""
            echo "🔄 Running reconnection tests with Deno..."
            ${pkgs.deno}/bin/deno test ./tests/reconnection.test.ts --no-check --allow-env --allow-net --allow-run || INTEGRATION_EXIT=$?
            
            # 結果サマリー
            echo ""
            echo "📊 Test Summary"
            echo "==============="
            echo "E2E Test: $([ $E2E_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
            echo "Integration Test: $([ $INTEGRATION_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
            echo ""
            
            if [ $E2E_EXIT -eq 0 ] && [ $INTEGRATION_EXIT -eq 0 ]; then
                echo "🎉 All tests passed!"
                exit 0
            else
                echo "❌ Some tests failed"
                exit 1
            fi
          ''}";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Deno for server and tests
            deno
            
            # Python for E2E tests
            pythonEnv
            
            # Development tools
            jq
            curl
            websocat  # WebSocket testing
          ];

          shellHook = ''
            echo "🔄 Unified Sync Development Environment"
            echo "====================================="
            echo ""
            echo "📦 Available tools:"
            echo "  - Deno ${pkgs.deno.version}"
            echo "  - Python ${pkgs.python311.version} with pytest"
            echo "  - websocat (WebSocket testing)"
            echo ""
            echo "🧪 Test commands:"
            echo "  nix run .#test              - Run all tests"
            echo "  pytest tests/e2e_test.py    - Run E2E tests only"
            echo "  deno test tests/            - Run integration tests"
            echo ""
          '';
        };
      });
}