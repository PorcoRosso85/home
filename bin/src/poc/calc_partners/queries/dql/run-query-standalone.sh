#!/usr/bin/env bash

# Standalone Cypher query runner - no node_modules required
# Uses npx to temporarily download and run kuzu-wasm

QUERY_FILE=$1

if [ -z "$QUERY_FILE" ]; then
  echo "Usage: ./run-query-standalone.sh <query-file.cypher>"
  exit 1
fi

# Create temporary Node.js script
cat > /tmp/kuzu-runner.js << 'EOF'
const fs = require('fs');
const kuzu = require('kuzu-wasm/nodejs');

(async () => {
  const queryFile = process.argv[2];
  const query = fs.readFileSync(queryFile, 'utf-8');
  
  await kuzu.init();
  const db = new kuzu.Database(':memory:', 1 << 30);
  const conn = new kuzu.Connection(db, 4);
  
  const result = await conn.query(query);
  const rows = await result.getAllObjects();
  
  console.log(JSON.stringify(rows, null, 2));
  
  await result.close();
  await conn.close();
  await db.close();
})();
EOF

# Run with npx - downloads kuzu-wasm temporarily, no node_modules created
npx --yes --package kuzu-wasm@latest node /tmp/kuzu-runner.js "$QUERY_FILE"

# Clean up
rm /tmp/kuzu-runner.js