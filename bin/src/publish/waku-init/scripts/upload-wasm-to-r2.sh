#!/bin/bash

# R2 WASM Upload Script
# Usage: ./upload-wasm-to-r2.sh

BUCKET_NAME="waku-wasm"
WASM_DIR="./wasm-files"

echo "🚀 Uploading WASM files to R2 bucket: $BUCKET_NAME"

# Create bucket if not exists
echo "📦 Creating R2 bucket (if not exists)..."
wrangler r2 bucket create $BUCKET_NAME 2>/dev/null || echo "Bucket already exists"

# Skip CORS configuration - configure manually if needed
echo "ℹ️  Skipping CORS configuration (configure manually if needed)"

# Upload DuckDB WASM files (if they exist)
if [ -d "$WASM_DIR/duckdb" ]; then
  echo "📤 Uploading DuckDB WASM files..."
  for file in $WASM_DIR/duckdb/*; do
    filename=$(basename "$file")
    echo "  Uploading: duckdb/$filename"
    wrangler r2 object put $BUCKET_NAME/duckdb/$filename --file="$file" \
      --content-type="$(file -b --mime-type "$file")"
  done
fi

# Upload SQLite WASM files (if they exist)
if [ -d "$WASM_DIR/sqlite" ]; then
  echo "📤 Uploading SQLite WASM files..."
  for file in $WASM_DIR/sqlite/*; do
    filename=$(basename "$file")
    echo "  Uploading: sqlite/$filename"
    wrangler r2 object put $BUCKET_NAME/sqlite/$filename --file="$file" \
      --content-type="$(file -b --mime-type "$file")"
  done
fi

# List uploaded files (using bucket list command)
echo ""
echo "📋 Bucket created successfully!"
echo "Note: Use 'wrangler r2 object get' to verify uploaded files"

echo ""
echo "✅ Upload complete!"
echo ""
echo "⚠️  Next steps:"
echo "1. Set up a custom domain for your R2 bucket in Cloudflare Dashboard"
echo "2. Add R2_WASM_URL to your environment variables:"
echo "   R2_WASM_URL=https://wasm.your-domain.com"
echo "3. Update wrangler.toml with the environment variable"