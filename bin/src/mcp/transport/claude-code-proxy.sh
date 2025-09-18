#!/usr/bin/env bash
# claude-code-proxy.sh
# Anthropic Claude Code MCPサーバーをHTTP/SSEプロキシ経由で実行するスクリプト

# エラーで終了するように設定
set -e

# デフォルト設定
ADDRESS="0.0.0.0"
PORT=8080
VERBOSE=false

# 引数のパース
while [[ $# -gt 0 ]]; do
  case $1 in
    --address|-a)
      ADDRESS="$2"
      shift 2
      ;;
    --port|-p)
      PORT="$2"
      shift 2
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Claude Code MCPサーバープロキシ"
      echo ""
      echo "使用方法: $0 [オプション]"
      echo ""
      echo "オプション:"
      echo "  --address, -a <address>  リッスンするアドレス (デフォルト: 0.0.0.0)"
      echo "  --port, -p <port>        リッスンするポート (デフォルト: 8080)"
      echo "  --verbose, -v            詳細なログ出力を有効にする"
      echo "  --help, -h               このヘルプメッセージを表示"
      echo ""
      echo "環境変数:"
      echo "  ANTHROPIC_API_KEY        AnthropicのAPIキー (Claude Codeに必要)"
      echo ""
      echo "例:"
      echo "  $0 --port 3000 --verbose"
      exit 0
      ;;
    *)
      echo "エラー: 不明なオプション $1"
      exit 1
      ;;
  esac
done

# 環境変数のチェック
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "警告: ANTHROPIC_API_KEY 環境変数が設定されていません。Claude Code MCPサーバーの実行に必要な場合があります。"
fi

# ランダムなセッションID生成関数
generate_session_id() {
  cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1
}

# 一時ディレクトリを作成
TMP_DIR=$(mktemp -d)
if [ "$VERBOSE" = true ]; then
  echo "一時ディレクトリ: $TMP_DIR"
fi
trap 'rm -rf "$TMP_DIR"; echo "一時ディレクトリを削除しました"; if [ -n "$MCP_PID" ]; then kill $MCP_PID 2>/dev/null || true; fi; if [ -n "$SERVER_PID" ]; then kill $SERVER_PID 2>/dev/null || true; fi; exit 0' EXIT

# プロキシサーバーで使用するSSEクライアントリスト
CLIENTS_FILE="$TMP_DIR/clients"
touch "$CLIENTS_FILE"

# エラーログファイル
ERROR_LOG="$TMP_DIR/error.log"

# Claude Code MCPサーバー起動 - 双方向の通信パイプを使用
echo "Claude Code MCPサーバーを起動中... (HTTP/SSEプロキシ: $ADDRESS:$PORT)"

# stdin/stdoutをパイプに接続するために名前付きパイプを作成
MCP_IN="$TMP_DIR/mcp_in"
MCP_OUT="$TMP_DIR/mcp_out"
mkfifo "$MCP_IN" "$MCP_OUT"

# 別プロセスでMCPサーバーを起動し、パイプに接続
( pnpx @anthropic-ai/claude-code mcp serve < "$MCP_IN" > "$MCP_OUT" 2> "$ERROR_LOG" ) &
MCP_PID=$!

echo "MCPサーバー起動 (PID: $MCP_PID)"

# 終了処理
cleanup() {
  echo "シャットダウン中..."
  if [ -n "$MCP_PID" ]; then
    kill $MCP_PID 2>/dev/null || true
  fi
  if [ -n "$SERVER_PID" ]; then
    kill $SERVER_PID 2>/dev/null || true
  fi
  exit 0
}

# SIGINTとSIGTERMのハンドラを設定
trap cleanup SIGINT SIGTERM

# MCPサーバーが起動するまで少し待機
sleep 2

# チェック
if ! ps -p $MCP_PID > /dev/null; then
  echo "エラー: Claude Code MCPサーバーの起動に失敗しました"
  cat "$ERROR_LOG"
  exit 1
fi

# SSEクライアントにメッセージを送信する関数
send_to_clients() {
  local event="$1"
  local data="$2"
  local message="event: $event
data: $data

"
  
  if [ "$VERBOSE" = true ]; then
    echo "[SSE送信] $event: $data"
  fi
  
  if [ -s "$CLIENTS_FILE" ]; then
    while read -r client_pipe; do
      echo "$message" > "$client_pipe" || true
    done < "$CLIENTS_FILE"
  fi
}

# 標準出力を監視して、SSEクライアントに転送
cat "$MCP_OUT" | while read -r line; do
  if [ "$VERBOSE" = true ]; then
    echo "[MCP出力] $line"
  fi
  
  # JSONかどうかをチェック
  if [[ "$line" == {*} ]]; then
    send_to_clients "message" "$line"
  fi
done &

# HTTPサーバー起動
echo "HTTP/SSEサーバーを起動中..."
{
  while true; do
    # nc -l で簡易HTTPサーバーを起動
    nc -l "$ADDRESS" "$PORT" | {
      # HTTPリクエストを受信
      read -r request_line
      if [ "$VERBOSE" = true ]; then
        echo "[HTTP] $request_line"
      fi
      
      # HTTPヘッダーを読み込む
      declare -A headers
      while read -r header_line; do
        header_line=${header_line%$'\r'}
        [ -z "$header_line" ] && break
        header_name="${header_line%%:*}"
        header_value="${header_line#*: }"
        headers["$header_name"]="$header_value"
      done
      
      # HTTPメソッドとパスを抽出
      request_method=$(echo "$request_line" | cut -d ' ' -f 1)
      request_path=$(echo "$request_line" | cut -d ' ' -f 2)
      
      if [ "$request_path" = "/sse" ] && [ "$request_method" = "GET" ]; then
        # SSE接続処理
        session_id=$(generate_session_id)
        client_pipe="$TMP_DIR/client_$session_id"
        mkfifo "$client_pipe"
        echo "$client_pipe" >> "$CLIENTS_FILE"
        
        # SSEレスポンスヘッダー
        cat << EOF
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

EOF
        
        # エンドポイント情報を送信
        cat << EOF
event: endpoint
data: http://$ADDRESS:$PORT/messages?sessionId=$session_id

event: connected
data: {"sessionId":"$session_id"}

EOF
        
        # クライアントパイプからの読み取り
        cat "$client_pipe"
        
        # 接続終了時の処理
        rm "$client_pipe"
        sed -i "\|^$client_pipe$|d" "$CLIENTS_FILE"
        
      elif [[ "$request_path" == /messages* ]] && [ "$request_method" = "POST" ]; then
        # メッセージ処理
        query="${request_path#*/messages}"
        session_id=$(echo "$query" | grep -o 'sessionId=[^&]*' | cut -d= -f2)
        
        # リクエストボディの長さを取得
        content_length="${headers[Content-Length]}"
        
        # リクエストボディを読み込む
        body=""
        if [ -n "$content_length" ] && [ "$content_length" -gt 0 ]; then
          body=$(dd bs=1 count="$content_length" 2>/dev/null)
        fi
        
        if [ "$VERBOSE" = true ]; then
          echo "[HTTP] Received message: $body"
        fi
        
        # メッセージをMCPサーバーに送信
        if [ "$VERBOSE" = true ]; then
          echo "[HTTP->MCP] 送信: $body"
        fi
        
        # 直接MCPサーバーの標準入力に書き込む
        echo "$body" > "$MCP_IN"
        
        # 受理レスポンス
        cat << EOF
HTTP/1.1 202 Accepted
Content-Type: application/json
Content-Length: 17

{"status":"accepted"}
EOF
      
      elif [ "$request_path" = "/healthz" ] && [ "$request_method" = "GET" ]; then
        # ヘルスチェック
        cat << EOF
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: 2

OK
EOF
      
      else
        # 404 Not Found
        cat << EOF
HTTP/1.1 404 Not Found
Content-Type: text/plain
Content-Length: 9

Not Found
EOF
      fi
    }
  done
} &
SERVER_PID=$!

echo "Claude Code MCPサーバーが起動しました"
echo "プロキシは $ADDRESS:$PORT でリッスン中です"
echo "SSEエンドポイント: http://$ADDRESS:$PORT/sse"
echo "SSEエンドポイント: http://$ADDRESS:$PORT/sse"
echo "デバッグ情報: $TMP_DIR"
echo "Ctrl+Cで停止できます"

# 初期化確認のために明示的なコマンドを送信
echo '{"jsonrpc":"2.0","method":"ping","id":0}' > "$MCP_IN"
if [ "$VERBOSE" = true ]; then
  echo "[初期化] pingリクエスト送信済み"
fi

# メインプロセスを実行し続ける
wait $MCP_PID
