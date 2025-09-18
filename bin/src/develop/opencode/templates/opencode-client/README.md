Dynamic opencode HTTP client (pre-auth assumed)

Overview
- Talks to a running opencode server via HTTP.
- Assumes authentication is already configured on the server side (no auth calls here).
- Keeps things dynamic via env vars and runtime discovery instead of static wrapping.

Quick start
- Ensure a server is running, e.g. Anthropic side on port 4096.
- Run: OPENCODE_URL=http://127.0.0.1:4096 ./client.sh "just say hi"
- Optional env:
  - OPENCODE_PROVIDER=anthropic
  - OPENCODE_MODEL=claude-3-5-sonnet

Design notes
- The script avoids hardcoding providers/models; it allows overrides via env.
- If provider/model are omitted, it relies on the server default selection.

GPT (future)
- This template intentionally omits any GPT specifics; add them later.

