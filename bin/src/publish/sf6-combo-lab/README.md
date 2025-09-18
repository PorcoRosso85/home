# SF6 Combo Lab

## 責務
ストリートファイター6のコンボ情報を構造化し、実用性を証明できるプラットフォーム

## コア機能
- **構造化投稿**: コンボデータの必須項目入力
- **再現報告**: 実用性の証明システム
- **効率計算**: ゲージ効率の自動算出
- **認証**: Google/X OAuth ソーシャルログイン
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
```

## Environment Variables

- `R2_WASM_URL`: URL for R2-hosted WASM files
- `ENABLE_WASM_FROM_R2`: Enable R2 WASM loading
- `MAX_ITEMS`: Counter component max value