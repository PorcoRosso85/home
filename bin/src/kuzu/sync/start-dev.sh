#!/bin/bash

# 開発・テスト用起動スクリプト
# Usage: ./start-dev.sh [command] [options]

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト設定
LOG_DIR="./logs"
DB_PATH="./test.db"
PORT=3000

# ヘルプメッセージ
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  server      サーバーを起動"
    echo "  test        テストを実行"
    echo "  clean       クリーンアップ処理"
    echo "  build       ビルド実行"
    echo "  dev         開発モード（ビルド + サーバー起動）"
    echo ""
    echo "Options:"
    echo "  --port PORT      サーバーポート (default: $PORT)"
    echo "  --db-path PATH   データベースパス (default: $DB_PATH)"
    echo "  --log-dir DIR    ログディレクトリ (default: $LOG_DIR)"
    echo "  --verbose        詳細ログ出力"
    echo "  --watch          ファイル変更を監視"
}

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ログディレクトリ作成
setup_logs() {
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        log_info "ログディレクトリを作成しました: $LOG_DIR"
    fi
}

# クリーンアップ処理
cleanup() {
    log_info "クリーンアップを開始します..."
    
    # テストデータベースの削除
    if [ -f "$DB_PATH" ]; then
        rm -f "$DB_PATH"
        log_info "テストデータベースを削除しました: $DB_PATH"
    fi
    
    # ログファイルの削除
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        log_info "ログディレクトリを削除しました: $LOG_DIR"
    fi
    
    # 一時ファイルの削除
    rm -f /tmp/export_*.parquet /tmp/export_*.csv
    
    # distディレクトリの削除
    if [ -d "./dist" ]; then
        rm -rf ./dist
        log_info "distディレクトリを削除しました"
    fi
    
    log_success "クリーンアップが完了しました"
}

# ビルド処理
build() {
    log_info "ビルドを開始します..."
    
    # TypeScriptコンパイル（必要に応じて追加）
    # pnpm tsc
    
    log_success "ビルドが完了しました"
}

# テスト実行
run_tests() {
    log_info "テストを実行します..."
    setup_logs
    
    # テストログファイル
    TEST_LOG="$LOG_DIR/test-$(date +%Y%m%d-%H%M%S).log"
    
    # テスト実行
    if [ "$VERBOSE" = true ]; then
        pnpm test 2>&1 | tee "$TEST_LOG"
    else
        pnpm test > "$TEST_LOG" 2>&1
    fi
    
    # テスト結果の確認
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "テストが成功しました"
        echo "詳細ログ: $TEST_LOG"
    else
        log_error "テストが失敗しました"
        echo "エラーログ: $TEST_LOG"
        tail -20 "$TEST_LOG"
        exit 1
    fi
}

# サーバー起動
start_server() {
    log_info "サーバーを起動します..."
    setup_logs
    
    # サーバーログファイル
    SERVER_LOG="$LOG_DIR/server-$(date +%Y%m%d-%H%M%S).log"
    
    # サーバー起動スクリプト（example-server.tsがある場合）
    if [ -f "./src/example-server.ts" ]; then
        log_info "サーバーをポート $PORT で起動します..."
        log_info "データベース: $DB_PATH"
        log_info "ログファイル: $SERVER_LOG"
        
        if [ "$VERBOSE" = true ]; then
            node --experimental-strip-types ./src/example-server.ts --port "$PORT" --db "$DB_PATH" 2>&1 | tee "$SERVER_LOG"
        else
            node --experimental-strip-types ./src/example-server.ts --port "$PORT" --db "$DB_PATH" > "$SERVER_LOG" 2>&1 &
            SERVER_PID=$!
            log_success "サーバーがPID $SERVER_PID で起動しました"
            echo "サーバーログ: tail -f $SERVER_LOG"
        fi
    else
        log_warning "サーバースクリプトが見つかりません"
        log_info "エクスポートサービスのテストサーバーを起動します..."
        
        # 簡易テストサーバーの作成
        cat > /tmp/test-server.js << 'EOF'
import { createExportService } from './dist/exportService.js';
import http from 'http';

const port = process.env.PORT || 3000;
const dbPath = process.env.DB_PATH || ':memory:';

async function startServer() {
    console.log(`Starting server on port ${port}...`);
    console.log(`Database path: ${dbPath}`);
    
    const server = http.createServer(async (req, res) => {
        if (req.url === '/health') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'ok', db: dbPath }));
        } else {
            res.writeHead(404);
            res.end('Not Found');
        }
    });
    
    server.listen(port, () => {
        console.log(`Server listening on http://localhost:${port}`);
    });
}

startServer().catch(console.error);
EOF
        
        PORT="$PORT" DB_PATH="$DB_PATH" node /tmp/test-server.js > "$SERVER_LOG" 2>&1 &
        SERVER_PID=$!
        log_success "テストサーバーがPID $SERVER_PID で起動しました"
    fi
}

# 開発モード
dev_mode() {
    log_info "開発モードを開始します..."
    
    # ビルド
    build
    
    # ウォッチモードの場合
    if [ "$WATCH" = true ]; then
        log_info "ファイル変更の監視を開始します..."
        # TypeScriptウォッチャー（必要に応じて追加）
        # pnpm tsc --watch &
        # TSC_PID=$!
    fi
    
    # サーバー起動
    start_server
    
    # 終了処理
    trap 'kill $SERVER_PID 2>/dev/null; exit' INT TERM
    
    # サーバーの監視
    wait $SERVER_PID
}

# 引数解析
COMMAND=""
VERBOSE=false
WATCH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        server|test|clean|build|dev)
            COMMAND=$1
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --db-path)
            DB_PATH="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --watch)
            WATCH=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# コマンド実行
case $COMMAND in
    server)
        start_server
        ;;
    test)
        run_tests
        ;;
    clean)
        cleanup
        ;;
    build)
        build
        ;;
    dev)
        dev_mode
        ;;
    *)
        log_error "コマンドを指定してください"
        show_help
        exit 1
        ;;
esac