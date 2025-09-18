{
  description = "Unified Sync - KuzuDB WASM + WebSocket + Event Store";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    storage-s3.url = "path:../../storage/s3";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
    log-ts.url = "path:../../telemetry/log_ts";
  };

  outputs = { self, nixpkgs, flake-utils, storage-s3, kuzu-ts, log-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Get the packaged kuzu_ts with pre-installed node_modules
        kuzuTsPackage = kuzu-ts.packages.${system}.default;
        # Get the Bun-specific package from persistence/kuzu_ts
        kuzuTsBunPackage = kuzu-ts.packages.${system}.bun;
        
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
            export PATH="${pkgs.deno}/bin:$PATH"
            export LOG_TS_PATH="${log-ts}/lib/mod.ts"
            echo "🚀 Starting KuzuDB sync server..."
            exec ${pkgs.deno}/bin/deno run --allow-net --allow-read --allow-env ./server.ts
          ''}";
        };
        
        # クライアント起動（Bun版）
        apps.client = {
          type = "app";
          program = "${pkgs.writeShellScript "start-client" ''
            # 環境設定（Bunのネイティブモジュール用）
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export LOG_TS_PATH="${log-ts}/lib/mod.ts"
            
            # node_modulesをリンク
            if [ ! -d node_modules ]; then
              mkdir -p node_modules
              ln -sf ${kuzuTsBunPackage}/lib/node_modules/kuzu node_modules/kuzu
            fi
            
            echo "🔌 Starting KuzuDB sync client (Bun)..."
            exec ${pkgs.bun}/bin/bun run ./client.ts $@
          ''}";
        };
        
        # Bunクライアント起動（persistence/kuzu_ts使用）
        apps.bun-client = {
          type = "app";
          program = "${pkgs.writeShellScript "start-bun-client" ''
            # 環境設定（persistence/kuzu_ts/examples/test_bun_package/flake.nixと同じ）
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # node_modulesをリンク
            if [ ! -d node_modules ]; then
              mkdir -p node_modules
              ln -sf ${kuzuTsBunPackage}/lib/node_modules/kuzu node_modules/kuzu
            fi
            
            echo "🐰 Starting KuzuDB sync client (Bun + persistence/kuzu_ts)..."
            exec ${pkgs.bun}/bin/bun run ./bun_client.ts $@
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
            export PATH="${pkgs.deno}/bin:$PATH"
            export LOG_TS_PATH="${log-ts}/lib/mod.ts"
            
            # ポート競合を避けるため、既存のプロセスをクリーンアップ
            echo "🧹 Cleaning up existing processes..."
            pkill -f "deno.*websocket-server" || true
            sleep 1
            
            # テスト結果
            INTEGRATION_EXIT=0
            
            
            # 統合テスト (TypeScript)
            echo ""
            echo "📦 Running integration tests with Deno..."
            ${pkgs.deno}/bin/deno test ./tests/websocket_sync.test.ts --no-check --trace-leaks --allow-env --allow-net --allow-run || INTEGRATION_EXIT=$?
            
            # 再接続テスト (TypeScript)
            echo ""
            echo "🔄 Running reconnection tests with Deno..."
            ${pkgs.deno}/bin/deno test ./tests/reconnection.test.ts --no-check --trace-leaks --allow-env --allow-net --allow-run || INTEGRATION_EXIT=$?
            
            # 結果サマリー
            echo ""
            echo "📊 Test Summary"
            echo "==============="
            echo "Integration Test: $([ $INTEGRATION_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
            echo ""
            
            if [ $INTEGRATION_EXIT -eq 0 ]; then
                echo "🎉 All tests passed!"
                exit 0
            else
                echo "❌ Some tests failed"
                exit 1
            fi
          ''}";
        };
        
        # サーバー付きテスト実行
        apps.test-with-server = {
          type = "app";
          program = "${pkgs.writeShellScript "test-with-server" ''
            set -e
            
            # Colors
            GREEN='\033[0;32m'
            RED='\033[0;31m'
            YELLOW='\033[1;33m'
            NC='\033[0m'
            
            echo -e "''${YELLOW}🚀 Starting test environment...''${NC}"
            
            # Cleanup function
            cleanup() {
              echo -e "\n''${YELLOW}🧹 Cleaning up...''${NC}"
              [ ! -z "''${SERVER_PID:-}" ] && kill $SERVER_PID 2>/dev/null || true
              exit ''${1:-0}
            }
            trap 'cleanup $?' EXIT INT TERM
            
            # Start server
            echo -e "''${GREEN}📡 Starting WebSocket server...''${NC}"
            ${pkgs.deno}/bin/deno run --allow-net --allow-read --allow-env ./server.ts &
            SERVER_PID=$!
            
            # Wait for server
            echo -e "''${YELLOW}⏳ Waiting for server...''${NC}"
            for i in {1..30}; do
              if ${pkgs.curl}/bin/curl -s http://localhost:8080/health > /dev/null 2>&1; then
                echo -e "''${GREEN}✅ Server ready!''${NC}"
                break
              fi
              [ $i -eq 30 ] && { echo -e "''${RED}❌ Server failed to start''${NC}"; exit 1; }
              sleep 0.5
            done
            
            # Run tests
            echo -e "''${GREEN}🧪 Running all tests...''${NC}"
            export PATH="${pkgs.deno}/bin:$PATH"
            export LOG_TS_PATH="${log-ts}/lib/mod.ts"
            
            # Run the existing test command
            nix run .#test
          ''}";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Deno for server and tests
            deno
            
            # Bun for client
            bun
            
            # Include the packaged kuzu_ts
            kuzuTsPackage
            # Include the Bun package from persistence/kuzu_ts
            kuzuTsBunPackage
            
            # System libraries for npm:kuzu
            stdenv.cc.cc.lib  # libstdc++.so.6
            
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
            echo "  nix run .#test-with-server  - Run tests with auto server"
            echo ""
            echo "📦 Available tools:"
            echo "  - Deno ${pkgs.deno.version}"
            echo "  - Bun ${pkgs.bun.version}"
            echo ""
            
            # Set environment variables for KuzuDB
            export KUZU_STORAGE_PATH="./kuzu_storage"
            export NODE_PATH="${kuzuTsPackage}/lib/node_modules:$NODE_PATH"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="${kuzuTsPackage}/lib"
            
            # Set up node_modules for Bun to use persistence/kuzu_ts
            if [ ! -d node_modules ]; then
              mkdir -p node_modules
              ln -sf ${kuzuTsBunPackage}/lib/node_modules/kuzu node_modules/kuzu
            fi
            
            # Set environment variable for log_ts module
            export LOG_TS_PATH="${log-ts}/lib/mod.ts"
            
            echo "📍 KuzuTS module: ${kuzuTsPackage}/lib/mod.ts"
            echo "📍 KuzuTS worker: ${kuzuTsPackage}/lib/mod_worker.ts"
            
          '';
        };
      });
}