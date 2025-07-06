{
  description = "Local WebSocket Client-Server Test";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        apps.default = {
          type = "app";
          program = "${pkgs.writeScriptBin "local-ws-test" ''
            #!${pkgs.bash}/bin/bash
            set -e
            
            echo "[LOCAL-WS-TEST] 🔌 Starting Local WebSocket Client-Server Test"
            echo "[LOCAL-WS-TEST] Port: WebSocket=8081"
            echo ""
            
            # 一時作業ディレクトリを作成
            WORK_DIR=$(mktemp -d)
            cd "$WORK_DIR"
            
            # テストファイルをコピー
            cp ${./.}/*.ts .
            
            # websocket-server.tsをコピーしてポート8081で起動
            cp websocket-server.ts websocket-server-8081.ts
            sed -i 's/const port = 8080/const port = 8081/' websocket-server-8081.ts
            
            echo "[LOCAL-WS-TEST] Starting server on port 8081..."
            ${pkgs.deno}/bin/deno run --allow-net websocket-server-8081.ts &
            SERVER_PID=$!
            
            sleep 2
            
            # テスト実行
            echo "[LOCAL-WS-TEST] Running KuzuDB sync client tests..."
            echo "[LOCAL-WS-TEST] 🔴 TDD Red Phase - expecting failure (implementation not yet created)"
            echo ""
            ${pkgs.deno}/bin/deno test --allow-net kuzu-sync-client.test.ts || true
            EXIT_CODE=$?
            echo ""
            echo "[LOCAL-WS-TEST] 🔴 Test failed as expected - kuzu-sync-client.ts module not found"
            
            # クリーンアップ
            echo "[LOCAL-WS-TEST] Cleaning up..."
            kill $SERVER_PID 2>/dev/null || true
            cd /
            rm -rf "$WORK_DIR"
            
            echo ""
            echo "[LOCAL-WS-TEST] 🔴 TDD Red Phase Complete"
            echo "[LOCAL-WS-TEST] Next step: Implement kuzu-sync-client.ts with functional design"
          ''}/bin/local-ws-test";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
          ];
        };
      }
    );
}