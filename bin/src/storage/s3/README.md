# S3 Storage Adapter

A TypeScript/Deno implementation providing a unified interface for S3-compatible storage services.

## Features

- **Protocol-based design**: Unified interface for multiple storage backends
- **Provider auto-detection**: Automatically detects AWS S3, MinIO, Cloudflare R2, Backblaze B2
- **LLM-first CLI**: JSON-based interface optimized for AI interaction
- **Type-safe**: Full TypeScript support with comprehensive type definitions

## Supported Providers

- AWS S3
- MinIO
- Cloudflare R2 (S3-compatible with zero egress fees)
- Backblaze B2
- Filesystem (local development)

Each provider is implemented as a separate module in the `providers/` directory.

## Usage

### As a Nix Flake

```nix
{
  inputs.s3-client.url = "path:/path/to/storage/s3";
  
  # Use the CLI
  packages.default = pkgs.writeShellScriptBin "my-app" ''
    ${s3-client.packages.${system}.default}/bin/s3-client "$@"
  '';
}
```

### CLI Usage

```bash
# Interactive mode
nix run .

# List objects
nix run . -- list --bucket my-bucket

# Upload file
nix run . -- upload --bucket my-bucket --key file.txt --file ./local.txt

# Download file
nix run . -- download --bucket my-bucket --key file.txt --output ./downloaded.txt

# Using with Cloudflare R2 (set environment variables)
export S3_ENDPOINT="https://<account-id>.r2.cloudflarestorage.com"
export AWS_ACCESS_KEY_ID="your-r2-access-key"
export AWS_SECRET_ACCESS_KEY="your-r2-secret-key"
nix run . -- list --bucket my-r2-bucket
```

### Programmatic Usage

```typescript
import { createS3Adapter } from "./mod.ts";
import { AWSProvider } from "./providers/aws-s3.ts";
import { MinIOProvider } from "./providers/minio.ts";
import { CloudflareR2Provider } from "./providers/cloudflare-r2.ts";

// Auto-detect provider from environment
const adapter = await createS3Adapter();

// Or specify a provider explicitly
const awsAdapter = await createS3Adapter({
  provider: new AWSProvider({
    endpoint: "https://s3.amazonaws.com",
    region: "us-east-1",
    credentials: {
      accessKeyId: "your-key",
      secretAccessKey: "your-secret",
    },
  }),
});

// Cloudflare R2 example (S3-compatible with zero egress fees)
const r2Adapter = await createS3Adapter({
  provider: new CloudflareR2Provider({
    endpoint: "https://<account-id>.r2.cloudflarestorage.com",
    region: "auto",
    credentials: {
      accessKeyId: "your-r2-access-key",
      secretAccessKey: "your-r2-secret-key",
    },
  }),
});

// Use the adapter
const objects = await adapter.listObjects("my-bucket");
await adapter.putObject("my-bucket", "file.txt", new TextEncoder().encode("Hello World"));
```

### Environment Variables

- `S3_ENDPOINT`: S3-compatible endpoint URL
- `AWS_ACCESS_KEY_ID`: Access key
- `AWS_SECRET_ACCESS_KEY`: Secret key
- `AWS_REGION`: AWS region (default: us-east-1)
- `S3_BUCKET`: Default bucket name

## Development

```bash
# Enter development shell
nix develop

# Run tests
nix run .#test

# Format code
nix run .#fmt

# Lint code
nix run .#lint
```

## Architecture

```
├── domain.ts               # Core types and interfaces
├── adapter.ts              # Storage adapter implementations
├── application.ts          # Use cases and business logic
├── infrastructure.ts       # AWS SDK integration
├── providers/              # Provider-specific implementations
│   ├── mod.ts             # Provider exports
│   ├── aws-s3.ts          # AWS S3 provider
│   ├── minio.ts           # MinIO provider
│   ├── cloudflare-r2.ts   # Cloudflare R2 provider
│   ├── backblaze-b2.ts    # Backblaze B2 provider
│   └── filesystem.ts      # Local filesystem provider
├── main.ts                 # CLI entry point
└── mod.ts                  # Public API exports
```

## Migration from Python

This module previously included a Python implementation that has been removed to maintain a single-language codebase. The TypeScript implementation provides equivalent functionality with better type safety and integration with Deno's built-in tooling.