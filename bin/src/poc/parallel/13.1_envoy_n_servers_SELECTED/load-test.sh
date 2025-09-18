#!/usr/bin/env bash
# 負荷テストスクリプト - N台構成の限界を探る

set -e

echo "🔥 POC 13.1: Load Test - Finding Envoy's limits with N servers"
echo "============================================================="
echo ""

# 結果ファイル
RESULTS_FILE="load-test-results.txt"
> $RESULTS_FILE

# テスト構成
test_configurations=(
    "3:1000"    # 3サーバー、1000リクエスト
    "5:5000"    # 5サーバー、5000リクエスト
    "10:10000"  # 10サーバー、10000リクエスト
    "20:20000"  # 20サーバー、20000リクエスト
)

for config in "${test_configurations[@]}"; do
    IFS=':' read -r servers requests <<< "$config"
    
    echo "📊 Testing with $servers servers, $requests requests"
    echo "================================================" | tee -a $RESULTS_FILE
    echo "Configuration: $servers servers, $requests requests" | tee -a $RESULTS_FILE
    
    # サーバーリストを生成
    SERVER_LIST=""
    for i in $(seq 1 $servers); do
        if [ $i -eq 1 ]; then
            SERVER_LIST="localhost:$((4000 + i))"
        else
            SERVER_LIST="$SERVER_LIST,localhost:$((4000 + i))"
        fi
    done
    
    # クリーンアップ
    pkill -f "test-server.ts" || true
    pkill -f "envoy-n-servers.ts" || true
    sleep 2
    
    # N台のサーバーを起動
    echo "Starting $servers servers..."
    ./start-n-servers.sh $servers &
    SERVERS_PID=$!
    sleep 3
    
    # Envoyプロキシを起動
    echo "Starting Envoy proxy..."
    BACKEND_SERVERS=$SERVER_LIST deno run --allow-net --allow-env envoy-n-servers.ts &
    PROXY_PID=$!
    sleep 3
    
    # 負荷テスト実行
    echo "Running load test..."
    START_TIME=$(date +%s)
    
    # vegeta attack
    echo "GET http://localhost:8080/" | vegeta attack -duration=30s -rate=$((requests/30))/s | \
        vegeta report | tee -a $RESULTS_FILE
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # 統計情報を取得
    echo -e "\nProxy Statistics:" | tee -a $RESULTS_FILE
    curl -s http://localhost:9901/stats | jq . | tee -a $RESULTS_FILE
    
    echo -e "\nTest Duration: ${DURATION}s" | tee -a $RESULTS_FILE
    echo -e "\n" | tee -a $RESULTS_FILE
    
    # クリーンアップ
    kill $PROXY_PID 2>/dev/null || true
    kill $SERVERS_PID 2>/dev/null || true
    pkill -f "test-server.ts" || true
    
    echo "Cooling down..."
    sleep 5
done

echo "🏁 Load test completed!"
echo "Results saved to: $RESULTS_FILE"

# 結果の要約
echo -e "\n📈 Summary of Results:"
echo "====================="
grep -E "Configuration:|Mean:|99th percentile:|Success:" $RESULTS_FILE