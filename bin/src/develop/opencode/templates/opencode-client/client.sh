#!/usr/bin/env bash
set -euo pipefail

# Dynamic opencode client sample (pre-auth assumed)
# - OPENCODE_URL: e.g. http://127.0.0.1:4096 (default)
# - OPENCODE_PROVIDER: optional, e.g. anthropic
# - OPENCODE_MODEL: optional, e.g. claude-3-5-sonnet

OPENCODE_URL="${OPENCODE_URL:-http://127.0.0.1:4096}"
MSG="${1:-just say hi}"
PROVIDER="${OPENCODE_PROVIDER:-}"
MODEL="${OPENCODE_MODEL:-}"

echo "[client] target: $OPENCODE_URL"

# 1) Health check
if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null; then
  echo "[client] error: server not reachable at $OPENCODE_URL" >&2
  exit 1
fi

# 2) Create session
SID=$(curl -fsS -X POST "$OPENCODE_URL/session" \
  -H 'Content-Type: application/json' \
  -d '{}' | jq -r '.id')
if [ -z "${SID:-}" ] || [ "$SID" = "null" ]; then
  echo "[client] error: failed to create session" >&2
  exit 1
fi
echo "[client] session: $SID"

# 3) Build message payload dynamically
PAYLOAD=$(jq -n --arg text "$MSG" --arg p "$PROVIDER" --arg m "$MODEL" '
  { parts: [{ type: "text", text: $text }] }
  + (if $p != "" and $m != "" then { model: { providerID: $p, modelID: $m }} else {} end)
')

# 4) Send message
RESP=$(curl -fsS -X POST "$OPENCODE_URL/session/$SID/message" \
  -H 'Content-Type: application/json' \
  -d "$PAYLOAD")

# 5) Extract a concise text response when available
if echo "$RESP" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
  echo "[client] reply:" && echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
else
  echo "$RESP" | jq
fi