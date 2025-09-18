#!/usr/bin/env bash

# Deployment script without D1 database
# The RedwoodSDK automatically adds D1, but it causes ES module errors

set -e

echo "Building for production..."
pnpm run clean
pnpm exec prisma generate
RWSDK_DEPLOY=1 pnpm run build

echo "Removing D1 database from wrangler config..."
# Remove D1 database section from generated wrangler.json
jq 'del(.d1_databases)' dist/worker/wrangler.json > dist/worker/wrangler.json.tmp
mv dist/worker/wrangler.json.tmp dist/worker/wrangler.json

echo "Deploying to Cloudflare Workers..."
pnpm exec wrangler deploy

echo "Deployment complete!"
echo "Access your app at: https://poc-redwoodsdk-duckdb.test-app-prod.workers.dev"