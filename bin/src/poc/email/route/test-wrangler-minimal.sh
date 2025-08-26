#!/usr/bin/env bash

echo "Testing wrangler with nix shell..."

# Create minimal worker
cat > minimal-worker.js << 'EOF'
export default {
  async fetch(request) {
    return new Response("Hello from minimal worker!");
  }
}
EOF

# Create minimal wrangler.toml
cat > minimal-wrangler.toml << 'EOF'
name = "minimal-worker"
main = "minimal-worker.js"
compatibility_date = "2024-01-01"
EOF

echo "Starting wrangler with nix shell..."
exec nix shell nixpkgs#wrangler --command wrangler dev --config minimal-wrangler.toml --local --port 8787