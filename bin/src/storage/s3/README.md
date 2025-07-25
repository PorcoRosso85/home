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
- Cloudflare R2
- Backblaze B2
- Filesystem (local development)

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
├── domain.ts       # Core types and interfaces
├── adapter.ts      # Storage adapter implementations
├── application.ts  # Use cases and business logic
├── infrastructure.ts # AWS SDK integration
├── main.ts         # CLI entry point
└── mod.ts          # Public API exports
```

## Migration from Python

This module previously included a Python implementation that has been removed to maintain a single-language codebase. The TypeScript implementation provides equivalent functionality with better type safety and integration with Deno's built-in tooling.