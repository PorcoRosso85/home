#!/usr/bin/env bash
# Test: AI Memory Token Verification
# Tests if AI can reliably recall specific tokens from previous messages

set -euo pipefail

echo "=== AI Memory Token Verification Test ==="
echo "Testing AI's ability to recall exact tokens from conversation history"
echo

OPENCODE_URL="http://127.0.0.1:4096"

# Step 1.2 RED: Token-based memory verification system
test_token_memory_system() {
    echo "🔬 Step 1.2: Testing Token Memory System (RED)"

    # Generate UUID for this test session
    local test_uuid
    if command -v uuidgen >/dev/null 2>&1; then
        test_uuid=$(uuidgen)
    else
        # Fallback UUID generation using random
        test_uuid="$(date +%s)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 1000-9999 -n 1)"
    fi

    local memory_token="TOKEN-${test_uuid}"
    echo "Generated memory token: $memory_token"

    # RED: This should initially fail - testing token recall capability
    echo "Phase 1: Establishing token memory..."

    # Create session
    if session_response=$(curl -fsS -X POST "$OPENCODE_URL/session" \
                         -H 'Content-Type: application/json' -d '{}'); then
        session_id=$(echo "$session_response" | jq -r '.id')
        echo "Session created: $session_id"

        # Step 2.2 RED: Low-ambiguity prompt design
        # Turn 1: Precise memory establishment with minimal ambiguity
        local memory_message="記憶用トークンは $memory_token です。この完全な文字列を正確に覚えてください。他には何も返答しないでください。"
        local message_payload="{\"parts\":[{\"type\":\"text\",\"text\":\"$memory_message\"}]}"

        echo "Sending low-ambiguity memory establishment message..."
        if turn1_response=$(curl -fsS -X POST "$OPENCODE_URL/session/$session_id/message" \
                          -H 'Content-Type: application/json' \
                          -d "$message_payload"); then
            echo "✅ Turn 1: Low-ambiguity memory establishment sent"

            # Check if AI responded (indicates AI provider is configured)
            if echo "$turn1_response" | jq -e '.parts[]? | select(.type=="text")' >/dev/null 2>&1; then
                local ai_response1=$(echo "$turn1_response" | jq -r '.parts[]? | select(.type=="text") | .text')
                echo "   AI Response 1 preview: $(echo "$ai_response1" | head -1 | cut -c1-60)..."

                # Step 2.2 RED: Ultra-precise recall prompt
                echo "Phase 2: Testing ultra-precise token recall..."

                local recall_message="先ほど覚えた記憶用トークンのみを、一字一句正確に、余計な文字・句読点・説明を一切含めず出力してください。トークン文字列のみです。"
                local recall_payload="{\"parts\":[{\"type\":\"text\",\"text\":\"$recall_message\"}]}"

                if turn2_response=$(curl -fsS -X POST "$OPENCODE_URL/session/$session_id/message" \
                                  -H 'Content-Type: application/json' \
                                  -d "$recall_payload"); then
                    echo "✅ Turn 2: Recall request sent"

                    # Check AI response for exact token match
                    if echo "$turn2_response" | jq -e '.parts[]? | select(.type=="text")' >/dev/null 2>&1; then
                        local ai_response2=$(echo "$turn2_response" | jq -r '.parts[]? | select(.type=="text") | .text')

                        echo "AI Response 2: '$ai_response2'"
                        echo "Expected Token: '$memory_token'"

                        # Step 3.3 GREEN: Ultra-precise full-text matching system
                        echo "🔍 Step 3: Ultra-precise full-text matching analysis..."
                        echo "   Expected: '$memory_token' (length: ${#memory_token})"
                        echo "   Received: '$ai_response2' (length: ${#ai_response2})"

                        # Multiple normalization strategies
                        local raw_response="$ai_response2"
                        local trimmed_response=$(echo "$ai_response2" | xargs)
                        local no_quotes_response=$(echo "$ai_response2" | sed 's/^["'\'']*//; s/["'\'']*$//')
                        local normalized_response=$(echo "$ai_response2" | tr -d '\n\r\t' | xargs)

                        echo "   Raw:        '$raw_response'"
                        echo "   Trimmed:    '$trimmed_response'"
                        echo "   No quotes:  '$no_quotes_response'"
                        echo "   Normalized: '$normalized_response'"

                        # Hierarchical matching (most strict to most lenient)
                        if [[ "$raw_response" == "$memory_token" ]]; then
                            echo "✅ SUCCESS: Perfect exact match (raw)"
                            return 0
                        elif [[ "$trimmed_response" == "$memory_token" ]]; then
                            echo "✅ SUCCESS: Exact match after whitespace trimming"
                            return 0
                        elif [[ "$no_quotes_response" == "$memory_token" ]]; then
                            echo "✅ SUCCESS: Exact match after quote removal"
                            return 0
                        elif [[ "$normalized_response" == "$memory_token" ]]; then
                            echo "✅ SUCCESS: Exact match after full normalization"
                            return 0
                        else
                            echo "❌ FAIL: No match found despite multiple normalization strategies"
                            echo "   🔬 Character-by-character diagnostic:"

                            # Enhanced character difference analysis
                            local max_len=$((${#memory_token} > ${#ai_response2} ? ${#memory_token} : ${#ai_response2}))
                            local diff_count=0

                            for ((i=0; i<max_len; i++)); do
                                exp_char="${memory_token:$i:1}"
                                rec_char="${ai_response2:$i:1}"

                                if [[ "$exp_char" != "$rec_char" ]]; then
                                    diff_count=$((diff_count + 1))
                                    printf "     [%02d] Expected: '%s' (ASCII: %d) | Received: '%s' (ASCII: %d)\n" \
                                        "$i" "$exp_char" "'$exp_char" "$rec_char" "'$rec_char" 2>/dev/null || \
                                    printf "     [%02d] Expected: '%s' | Received: '%s'\n" "$i" "$exp_char" "$rec_char"
                                fi
                            done

                            echo "   📊 Summary: $diff_count character differences out of $max_len total"

                            # Similarity analysis
                            if [[ $max_len -gt 0 ]]; then
                                local similarity=$((100 * (max_len - diff_count) / max_len))
                                echo "   📈 Similarity: ${similarity}%"
                            fi

                            return 1
                        fi
                    else
                        echo "❌ FAIL: No AI response text in turn 2"
                        return 1
                    fi
                else
                    echo "❌ FAIL: Turn 2 request failed"
                    return 1
                fi
            else
                echo "⚠️  WARNING: No AI response - AI provider not configured"
                echo "   This test requires AI provider setup to verify memory recall"
                echo "   Infrastructure test: Session and message sending works"
                return 1
            fi
        else
            echo "❌ FAIL: Turn 1 request failed"
            return 1
        fi
    else
        echo "❌ FAIL: Session creation failed"
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

# Run token memory test
echo "🔄 Running Token Memory System Test"
if test_token_memory_system; then
    echo
    echo "🟢 Token Memory System: VERIFIED ✅"
    echo "   AI can reliably recall exact tokens from conversation history"
else
    echo
    echo "🔴 Token Memory System: NEEDS SETUP ❌"
    echo "   Either AI provider not configured or memory recall imprecise"
fi

echo
echo "🏁 AI Memory Token Verification Test Completed!"
echo "   This test verifies AI's ability to recall specific information"
echo "   from previous messages with high precision and reliability."