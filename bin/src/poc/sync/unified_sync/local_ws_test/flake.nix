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
            cp ${./.}/*.ts . || true
            # 実装ファイルもコピー
            cp ${./kuzu-sync-client.ts} . || true
            # 追加ファイルもコピー
            cp ${./sync-verification-design.md} . || true
            
            # コピーされたファイルを確認
            echo "[LOCAL-WS-TEST] Files in working directory:"
            ls -la *.ts || true
            
            # websocket-server.tsをコピーしてポート8081で起動
            cp websocket-server.ts websocket-server-8081.ts
            sed -i 's/const port = 8080/const port = 8081/' websocket-server-8081.ts
            
            # ポート8081のプロセスを先に終了
            ${pkgs.lsof}/bin/lsof -ti:8081 | xargs -r kill -9 2>/dev/null || true
            
            echo "[LOCAL-WS-TEST] Starting server on port 8081..."
            ${pkgs.deno}/bin/deno run --allow-net websocket-server-8081.ts &
            SERVER_PID=$!
            
            sleep 2
            
            # テスト実行
            echo "[LOCAL-WS-TEST] Running KuzuDB sync client tests..."
            echo "[LOCAL-WS-TEST] 🟢 TDD Green Phase - running implementation"
            echo ""
            ${pkgs.deno}/bin/deno test --no-check --allow-net --allow-read kuzu-sync-client.test.ts
            EXIT_CODE=$?
            
            # クリーンアップ
            echo "[LOCAL-WS-TEST] Cleaning up..."
            kill $SERVER_PID 2>/dev/null || true
            cd /
            rm -rf "$WORK_DIR"
            
            if [ $EXIT_CODE -eq 0 ]; then
              echo ""
              echo "[LOCAL-WS-TEST] ✅ All tests passed!"
            else
              echo ""
              echo "[LOCAL-WS-TEST] ❌ Tests failed"
              exit 1
            fi
          ''}/bin/local-ws-test";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            lsof
          ];
        };
      }
    );
}