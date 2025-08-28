# Waku + Cloudflare Workers + R2 Boilerplate

React Server Components with Cloudflare Workers and R2 storage integration.

## Prerequisites

This project uses Nix for dependency management. Install Nix:
```bash
curl -L https://nixos.org/nix/install | sh
```

## Quick Start

```bash
# Development
npm install
npm run dev         # Waku dev server (port 3000)
npm run start:nix   # Wrangler dev with R2 (port 8787)

# Build
npm run build

# Deploy to Cloudflare
nix shell nixpkgs#wrangler -c wrangler deploy
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

## Wrangler Commands

All wrangler commands require Nix:
```bash
# Type generation
nix shell nixpkgs#wrangler -c wrangler types

# R2 management
nix shell nixpkgs#wrangler -c wrangler r2 bucket create waku-data
nix shell nixpkgs#wrangler -c wrangler r2 object list waku-data

# D1 database
nix shell nixpkgs#wrangler -c wrangler d1 execute init --file=./migrations/ddl.sql
```

## CI/CD Setup

For GitHub Actions or other CI:
```yaml
- uses: cachix/install-nix-action@v20
- run: nix shell nixpkgs#nodejs nixpkgs#wrangler -c npm run build
- run: nix shell nixpkgs#wrangler -c wrangler deploy
```

## Environment Variables

- `R2_WASM_URL`: URL for R2-hosted WASM files
- `ENABLE_WASM_FROM_R2`: Enable R2 WASM loading
- `MAX_ITEMS`: Counter component max value

## Development

The project intentionally excludes wrangler from node_modules to ensure consistent versions via Nix.