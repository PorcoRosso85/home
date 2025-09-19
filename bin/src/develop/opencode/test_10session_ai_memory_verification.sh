#!/usr/bin/env bash
# Test: 10 Session AI Memory Verification (Complete)
# Combines parallel infrastructure with AI token-based memory verification

set -euo pipefail

echo "=== 10 Session AI Memory Verification (Complete) ==="
echo "Testing AI memory recall across 10 parallel sessions with token verification"
echo

OPENCODE_URL="http://127.0.0.1:4096"

# Step 4.2 RED: 10 Session parallel AI memory verification
test_parallel_ai_memory() {
    echo "🔬 Step 4.2: Testing 10 Session Parallel AI Memory Verification"

    declare -A session_ids
    declare -A memory_tokens
    declare -a pids

    echo "Phase 1: Creating 10 sessions with unique memory tokens..."

    # Phase 1: Create sessions and establish unique memory tokens
    for i in {1..10}; do
        (
            local session_num=$(printf '%02d' $i)
            local delay=$(echo "scale=1; $i * 0.1" | bc -l)
            sleep "$delay"

            # Generate unique token for this session
            local test_uuid
            if command -v uuidgen >/dev/null 2>&1; then
                test_uuid=$(uuidgen | tr -d '-')
            else
                test_uuid="$(date +%s)$(shuf -i 1000-9999 -n 1)${session_num}"
            fi

            local memory_token="TOKEN-S${session_num}-${test_uuid:0:8}"
            echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Token=$memory_token"

            # Create session
            if session_response=$(curl -fsS -X POST "$OPENCODE_URL/session" \
                                 -H 'Content-Type: application/json' -d '{}'); then
                session_id=$(echo "$session_response" | jq -r '.id')
                echo "[$(date '+%H:%M:%S.%3N')] Session $session_num created: $session_id"

                # Turn 1: Send token for memorization
                local memory_message="記憶用トークンは $memory_token です。この完全な文字列を正確に覚えてください。他には何も返答しないでください。"
                local message_payload="{\"parts\":[{\"type\":\"text\",\"text\":\"$memory_message\"}]}"

                if curl -fsS -X POST "$OPENCODE_URL/session/$session_id/message" \
                        -H 'Content-Type: application/json' \
                        -d "$message_payload" >/dev/null 2>&1; then
                    echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Token memorization sent"
                    echo "$session_id" > "/tmp/session_${session_num}_id.txt"
                    echo "$memory_token" > "/tmp/session_${session_num}_token.txt"
                    echo "memorized" > "/tmp/session_${session_num}_phase1.txt"
                else
                    echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Token memorization failed"
                    echo "failed" > "/tmp/session_${session_num}_phase1.txt"
                fi
            else
                echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Session creation failed"
                echo "creation_failed" > "/tmp/session_${session_num}_phase1.txt"
            fi
        ) &
        pids+=($!)
    done

    # Wait for phase 1
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    echo "Phase 2: Testing AI memory recall across all sessions..."

    # Reset pids for phase 2
    pids=()

    # Phase 2: Test memory recall in parallel
    for i in {1..10}; do
        (
            local session_num=$(printf '%02d' $i)

            if [[ -f "/tmp/session_${session_num}_phase1.txt" ]] && [[ "$(cat "/tmp/session_${session_num}_phase1.txt")" == "memorized" ]]; then
                local session_id=$(cat "/tmp/session_${session_num}_id.txt")
                local expected_token=$(cat "/tmp/session_${session_num}_token.txt")
                local delay=$(echo "scale=1; $i * 0.1" | bc -l)
                sleep "$delay"

                echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Testing memory recall..."

                # Turn 2: Request token recall
                local recall_message="先ほど覚えた記憶用トークンのみを、一字一句正確に、余計な文字・句読点・説明を一切含めず出力してください。トークン文字列のみです。"
                local recall_payload="{\"parts\":[{\"type\":\"text\",\"text\":\"$recall_message\"}]}"

                if response=$(curl -fsS -X POST "$OPENCODE_URL/session/$session_id/message" \
                            -H 'Content-Type: application/json' \
                            -d "$recall_payload"); then

                    # Check AI response
                    if echo "$response" | jq -e '.parts[]? | select(.type=="text")' >/dev/null 2>&1; then
                        local ai_response=$(echo "$response" | jq -r '.parts[]? | select(.type=="text") | .text')

                        echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: AI responded"
                        echo "$ai_response" > "/tmp/session_${session_num}_response.txt"
                        echo "$expected_token" > "/tmp/session_${session_num}_expected.txt"

                        # Quick match check
                        local trimmed_response=$(echo "$ai_response" | xargs)
                        local no_quotes_response=$(echo "$ai_response" | sed 's/^["'\'']*//; s/["'\'']*$//')

                        if [[ "$ai_response" == "$expected_token" ]] || \
                           [[ "$trimmed_response" == "$expected_token" ]] || \
                           [[ "$no_quotes_response" == "$expected_token" ]]; then
                            echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Memory recall SUCCESS"
                            echo "success" > "/tmp/session_${session_num}_phase2.txt"
                        else
                            echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Memory recall FAILED"
                            echo "mismatch" > "/tmp/session_${session_num}_phase2.txt"
                        fi
                    else
                        echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: No AI response"
                        echo "no_response" > "/tmp/session_${session_num}_phase2.txt"
                    fi
                else
                    echo "[$(date '+%H:%M:%S.%3N')] Session $session_num: Recall request failed"
                    echo "request_failed" > "/tmp/session_${session_num}_phase2.txt"
                fi
            fi
        ) &
        pids+=($!)
    done

    # Wait for phase 2
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    echo "Phase 3: Analyzing 10-session AI memory results..."

    # Phase 3: Comprehensive analysis
    local total_sessions=0
    local successful_memory=0
    local ai_response_count=0
    declare -A unique_tokens

    for i in {1..10}; do
        local session_num=$(printf '%02d' $i)

        if [[ -f "/tmp/session_${session_num}_phase1.txt" ]] && [[ "$(cat "/tmp/session_${session_num}_phase1.txt")" == "memorized" ]]; then
            total_sessions=$((total_sessions + 1))
            local expected_token=$(cat "/tmp/session_${session_num}_expected.txt" 2>/dev/null || echo "unknown")
            unique_tokens["$expected_token"]=1

            if [[ -f "/tmp/session_${session_num}_phase2.txt" ]]; then
                local phase2_status=$(cat "/tmp/session_${session_num}_phase2.txt")

                case "$phase2_status" in
                    "success")
                        ai_response_count=$((ai_response_count + 1))
                        successful_memory=$((successful_memory + 1))
                        echo "✅ Session $session_num: Perfect AI memory recall"
                        echo "   Token: $expected_token"
                        ;;
                    "mismatch")
                        ai_response_count=$((ai_response_count + 1))
                        local ai_response=$(cat "/tmp/session_${session_num}_response.txt" 2>/dev/null || echo "unknown")
                        echo "❌ Session $session_num: AI memory mismatch"
                        echo "   Expected: $expected_token"
                        echo "   Received: $ai_response"
                        ;;
                    "no_response")
                        echo "⚠️  Session $session_num: No AI response (provider issue)"
                        ;;
                    "request_failed")
                        echo "❌ Session $session_num: Request failed"
                        ;;
                    *)
                        echo "❓ Session $session_num: Unknown status ($phase2_status)"
                        ;;
                esac
            else
                echo "❌ Session $session_num: No phase 2 data"
            fi
        fi
    done

    # Cleanup
    rm -f /tmp/session_*_*.txt

    # Calculate metrics
    local unique_token_count=${#unique_tokens[@]}
    local memory_success_rate=0
    local ai_response_rate=0

    if [[ $total_sessions -gt 0 ]]; then
        memory_success_rate=$(echo "scale=1; ($successful_memory * 100) / $total_sessions" | bc -l)
        ai_response_rate=$(echo "scale=1; ($ai_response_count * 100) / $total_sessions" | bc -l)
    fi

    echo
    echo "🏆 10-Session AI Memory Results:"
    echo "   Total sessions: $total_sessions"
    echo "   AI responses: $ai_response_count ($ai_response_rate%)"
    echo "   Successful memory: $successful_memory ($memory_success_rate%)"
    echo "   Unique tokens: $unique_token_count (cross-talk check)"

    # Success criteria
    if [[ $ai_response_count -eq 0 ]]; then
        echo "⚠️  WARNING: No AI responses - AI provider not configured"
        echo "   Infrastructure: Session creation and messaging work correctly"
        echo "   To test AI memory: Configure AI provider and re-run"
        return 1
    elif [[ $successful_memory -eq $total_sessions ]] && [[ $total_sessions -eq 10 ]] && [[ $unique_token_count -eq 10 ]]; then
        echo "✅ SUCCESS: Perfect AI memory across all 10 parallel sessions"
        echo "   - AI memory recall: 100% success"
        echo "   - Session isolation: 100% verified (no cross-talk)"
        echo "   - Parallel processing: 100% functional"
        return 0
    else
        echo "❌ ISSUES: AI memory not perfect across sessions"
        echo "   Expected: 10/10 sessions with perfect memory + no cross-talk"
        echo "   Actual: $successful_memory/$total_sessions successful, $unique_token_count unique tokens"
        return 1
    fi
}

# Server health check
if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null 2>&1; then
    echo "❌ Server not accessible at $OPENCODE_URL"
    exit 1
fi

echo "✅ Server responding"
echo

# Run complete AI memory verification
echo "🔄 Running Complete 10-Session AI Memory Verification"
if test_parallel_ai_memory; then
    echo
    echo "🟢 10-Session AI Memory: PERFECT ✅"
    echo "   AI reliably recalls tokens across all parallel sessions"
else
    echo
    echo "🔴 10-Session AI Memory: NEEDS ATTENTION ❌"
    echo "   Either AI provider setup needed or memory issues detected"
fi

echo
echo "🏁 Complete AI Memory Verification Test Completed!"
echo "   This test verifies that AI can reliably recall specific tokens"
echo "   from conversation history across 10 parallel sessions, ensuring"
echo "   both session isolation and memory reliability under load."