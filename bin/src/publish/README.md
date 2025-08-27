# Publish Directory

## Core

- **Purpose**: Deploy to `trst.worker.dev`
- **Method**: Individual directory deployment  
- **Infrastructure**: Cloudflare Workers
- **Scope**: Service directory management only

## Structure

```
publish/
├── flake.nix          # Directory management tooling
└── [service-dirs]/    # Each service with own deployment responsibility
```

## Per-Service Responsibility

Each service directory handles:
- Own framework decisions
- Deployment configuration
- Build scripts
- Environment variables
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