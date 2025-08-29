# Waku + Cloudflare Workers + R2 Boilerplate

React Server Components with Cloudflare Workers and R2 storage integration.

## 責務範囲

このプロジェクトは**アプリケーション実装例**です。以下は責務外です：

- **CI/CD設定**: `waku_node` (基盤層) が提供
- **Nix環境管理**: `waku_node` のflake.nixを参照
- **ビルドツール**: `nix run .#build` / `nix run .#deploy` を使用

詳細は [waku_node](../../poc/vite_rsc/waku_node/) を参照してください。

## Quick Start

```bash
# Install dependencies
npm install

# Development
npm run dev         # Waku dev server (port 3000)
npm run start:nix   # Wrangler dev with R2 (port 8787)

# Build
nix run .#build

# Deploy
nix run .#deploy
```

## Features

- React Server Components with Waku
- Cloudflare Workers deployment
- R2 storage for WASM files and form submissions
- D1 database support
- Lazy-loaded DuckDB and SQLite WASM
- Feedback and Contact forms with R2 append-only storage

## Architecture

```
Browser → Waku RSC → Worker → R2/D1
           ↓
       Server Actions → R2 Storage
```

## R2 Form Storage

Forms are stored in R2 with timestamp-based paths:
```
submissions/YYYY/MM/DD/timestamp-uuid.json
```

## Development Commands

```bash
# R2 management
nix shell nixpkgs#wrangler -c wrangler r2 bucket create waku-data
nix shell nixpkgs#wrangler -c wrangler r2 object list waku-data

# D1 database
nix shell nixpkgs#wrangler -c wrangler d1 execute init --file=./migrations/ddl.sql

# Log streaming (JSON output)
bin/wrangler-tail-json <worker-name>     # Stream logs as JSON
bin/wrangler-tail-json <worker-name> 10  # Stream for 10 seconds
```

## Tools

### bin/wrangler-tail-json
Streams Cloudflare Worker logs as clean JSON for analysis:

```bash
# Basic usage
bin/wrangler-tail-json my-worker

# Pipe to analysis tools
bin/wrangler-tail-json my-worker | jq '.logs | length'
bin/wrangler-tail-json my-worker | duckdb -c "SELECT * FROM read_json_auto('/dev/stdin')"
```

## Environment Variables

- `R2_WASM_URL`: URL for R2-hosted WASM files
- `ENABLE_WASM_FROM_R2`: Enable R2 WASM loading
- `MAX_ITEMS`: Counter component max value