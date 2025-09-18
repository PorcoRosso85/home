#!/usr/bin/env nix-shell
#!nix-shell -i bash -p wrangler

echo "Testing wrangler from nixpkgs..."
echo "Wrangler version:"
wrangler --version

echo ""
echo "Testing wrangler dev with simple worker..."

# Create minimal test worker
cat > test-worker.js << 'EOF'
export default {
  async fetch(request) {
    return new Response("Hello from minimal worker!");
  }
}
EOF

# Create minimal wrangler.toml
cat > test-wrangler.toml << 'EOF'
name = "test-worker"
main = "test-worker.js"
compatibility_date = "2024-01-01"
EOF

echo "Starting wrangler dev server..."
wrangler dev --config test-wrangler.toml --local --port 8787