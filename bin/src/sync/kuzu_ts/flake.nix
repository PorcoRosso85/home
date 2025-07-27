{
  description = "Unified Sync - KuzuDB WASM + WebSocket + Event Store";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    storage-s3.url = "path:../../storage/s3";
    kuzu-py.url = "path:../../persistence/kuzu_py";
    log-ts.url = "path:../../telemetry/log_ts";
  };

  outputs = { self, nixpkgs, flake-utils, storage-s3, kuzu-py, log-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境 - kuzu-pyを含めた統合環境
        # kuzu-pyはkuzuPyパッケージとして提供される
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # kuzu-pyからのパッケージ
          kuzu-py.packages.${system}.kuzuPy
          # 既存のテスト用パッケージ
          pytest
          pytest-asyncio
          websockets
          httpx
          aiohttp
        ]);
        
      in
      {
        # デフォルトアプリ（利用可能なコマンド一覧を表示）
        apps.default = {
          type = "app";
          program = let
            appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
            helpText = ''
              🔄 KuzuDB Sync - 分散同期システム
              
              利用可能なコマンド:
              ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
            '';
          in "${pkgs.writeShellScript "show-help" ''
            cat << 'EOF'
            ${helpText}
            EOF
          ''}";
        };
        
        # サーバー起動
        apps.server = {
          type = "app";
          program = "${pkgs.writeShellScript "start-server" ''
            export LOG_TS_PATH="${log-ts.lib.importPath}"
            export PATH="${pkgs.deno}/bin:$PATH"
            echo "🚀 Starting KuzuDB sync server..."
            exec ${pkgs.deno}/bin/deno run --allow-net --allow-read --allow-env ./server.ts
          ''}";
        };
        
        # クライアント起動
        apps.client = {
          type = "app";
          program = "${pkgs.writeShellScript "start-client" ''
            export PATH="${pkgs.deno}/bin:$PATH"
            echo "🔌 Starting KuzuDB sync client..."
            exec ${pkgs.deno}/bin/deno run --allow-net ./client.ts $@
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
            echo "🔄 KuzuDB Sync Development Environment"
            echo "====================================="
            echo ""
            echo "🚀 Quick start:"
            echo "  nix run .#server            - Start sync server"
            echo "  nix run .#client            - Start sync client"
            echo "  nix run .#test              - Run all tests"
            echo ""
            echo "📦 Available tools:"
            echo "  - Deno ${pkgs.deno.version}"
            echo "  - Python ${pkgs.python312.version} with pytest"
            echo "  - KuzuDB (Python bindings)"
            echo ""
            
            # Set environment variables for KuzuDB
            export KUZU_STORAGE_PATH="./kuzu_storage"
            export NODE_PATH="${pkgs.nodejs}/lib/node_modules:$NODE_PATH"
            
            # Set environment variable for log_ts module
            export LOG_TS_PATH="${log-ts.lib.importPath}"
          '';
        };
      });
}