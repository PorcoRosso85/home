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
        apps.test = {
          type = "app";
          program = "${pkgs.writeScriptBin "local-ws-test" ''
            #!${pkgs.bash}/bin/bash
            set -e
            
            echo "[LOCAL-WS-TEST] 🔌 Starting Local WebSocket Client-Server Test"
            echo "[LOCAL-WS-TEST] Port: WebSocket=8081"
            echo ""
            
            # 作業ディレクトリ（テストファイルがあるディレクトリ）
            cd ${./.}
            
            # websocket-server.tsをコピーしてポート8081で起動
            cp websocket-server.ts websocket-server-8081.ts
            sed -i 's/const port = 8080/const port = 8081/' websocket-server-8081.ts
            
            echo "[LOCAL-WS-TEST] Starting server on port 8081..."
            ${pkgs.deno}/bin/deno run --allow-net websocket-server-8081.ts &
            SERVER_PID=$!
            
            sleep 2
            
            # テスト実行
            echo "[LOCAL-WS-TEST] Running WebSocket client tests..."
            ${pkgs.deno}/bin/deno run --allow-net test-ws-client.ts
            EXIT_CODE=$?
            
            # クリーンアップ
            echo "[LOCAL-WS-TEST] Cleaning up..."
            kill $SERVER_PID 2>/dev/null || true
            rm -f websocket-server-8081.ts
            
            if [ $EXIT_CODE -eq 0 ]; then
              echo "[LOCAL-WS-TEST] ✅ Test PASSED"
            else
              echo "[LOCAL-WS-TEST] ❌ Test FAILED"
              exit 1
            fi
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