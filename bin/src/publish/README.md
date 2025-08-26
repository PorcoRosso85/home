# Publish Directory

## Core

- **Purpose**: Deploy to `trst.worker.dev`
- **Method**: Individual directory deployment  
- **Infrastructure**: Cloudflare Workers

## Structure

```
publish/
├── flake.nix          # Deployment tooling
└── [service-dirs]/    # Each independently deployable
```

## Framework Base

- **Input**: `/home/nixos/bin/src/poc/vite_rsc/waku_node`
- **Method**: flake.input継承
- **Delegation**: フレームワーク・ビルド・デプロイは先方
- **Customization**: ロジック・コンポーネントのみこちらで実装

## Per-Service Requirements

- Own deployment config
- Environment variables
- Build scripts
- Documentation

## URL Mapping

- Main: `https://trst.worker.dev`
- Services: `https://trst.worker.dev/{service}`

## Workflow

1. Develop: `/home/nixos/bin/src/{service}`
2. Configure: `/home/nixos/bin/src/publish/{service}`
3. Deploy: `trst.worker.dev`

## Security

- Defensive security only
- No malicious code
- Protected environment variables