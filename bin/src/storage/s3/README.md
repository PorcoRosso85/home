# S3 Storage Module

An LLM-first interface for S3 operations with interactive JSON-based commands.

## Features

- **LLM-Optimized**: JSON-based interface designed for easy interaction with language models
- **Interactive Mode**: User-friendly CLI with examples and help
- **Full S3 Support**: List, upload, download, delete, and get info operations
- **S3-Compatible**: Works with AWS S3, MinIO, and other S3-compatible services
- **Type-Safe**: Written in TypeScript with comprehensive type definitions

## Installation

```bash
# Using Nix
nix run

# Using Deno directly
deno run --allow-all main.ts
```

## Configuration

Set the following environment variables:

```bash
export S3_REGION="us-east-1"
export S3_ACCESS_KEY_ID="your-access-key"
export S3_SECRET_ACCESS_KEY="your-secret-key"
export S3_BUCKET="your-bucket-name"

# Optional: For S3-compatible services like MinIO
export S3_ENDPOINT="http://localhost:9000"
```

## Usage

### Interactive Mode

```bash
nix run
# or
deno run --allow-all main.ts
```

### Direct Command Mode

```bash
# List objects
nix run . '{"action": "list", "prefix": "photos/"}'

# Upload a file
nix run . '{"action": "upload", "key": "test.txt", "content": "Hello, S3!"}'

# Download a file
nix run . '{"action": "download", "key": "test.txt"}'

# Get object info
nix run . '{"action": "info", "key": "test.txt"}'

# Delete objects
nix run . '{"action": "delete", "keys": ["test.txt"]}'
```

### Pipe Mode

```bash
echo '{"action": "list"}' | nix run
```

## Command Reference

### List Objects
```json
{
  "action": "list",
  "prefix": "photos/",      // Optional: Filter by prefix
  "maxKeys": 100,           // Optional: Limit results
  "continuationToken": "..."// Optional: For pagination
}
```

### Upload Object
```json
{
  "action": "upload",
  "key": "documents/report.pdf",
  "content": "base64-encoded-content",
  "contentType": "application/pdf",    // Optional
  "metadata": {                        // Optional
    "author": "John Doe"
  }
}
```

### Download Object
```json
{
  "action": "download",
  "key": "documents/report.pdf",
  "outputPath": "./report.pdf"  // Optional: Save to file
}
```

### Delete Objects
```json
{
  "action": "delete",
  "keys": ["temp/file1.txt", "temp/file2.txt"]
}
```

### Get Object Info
```json
{
  "action": "info",
  "key": "documents/report.pdf"
}
```

### Help
```json
{
  "action": "help"
}
```

## Examples

### Upload and verify a file
```bash
# Upload
echo '{"action": "upload", "key": "test.txt", "content": "Hello, World!"}' | nix run

# Verify
echo '{"action": "info", "key": "test.txt"}' | nix run

# Download
echo '{"action": "download", "key": "test.txt"}' | nix run
```

### List and delete old files
```bash
# List files with prefix
echo '{"action": "list", "prefix": "temp/"}' | nix run

# Delete specific files
echo '{"action": "delete", "keys": ["temp/old1.txt", "temp/old2.txt"]}' | nix run
```

## Development

```bash
# Run tests
deno task test

# Format code
deno task fmt

# Lint code
deno task lint

# Development mode with auto-reload
deno task dev
```

## Architecture

The module follows a clean architecture pattern:

- `main.ts` - CLI entry point with interactive mode
- `mod.ts` - Public API exports
- `domain.ts` - Type definitions and business logic
- `application.ts` - Use cases and command execution
- `infrastructure.ts` - AWS SDK integration
- `variables.ts` - Environment configuration

## Error Handling

All errors are returned as JSON for easy parsing:

```json
{
  "type": "error",
  "message": "Object not found",
  "details": {
    "key": "missing-file.txt"
  }
}
```

## Testing with MinIO

For local development, you can use MinIO:

```bash
# Start MinIO
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address :9001

# Configure for MinIO
export S3_ENDPOINT="http://localhost:9000"
export S3_REGION="us-east-1"
export S3_ACCESS_KEY_ID="minioadmin"
export S3_SECRET_ACCESS_KEY="minioadmin"
export S3_BUCKET="test-bucket"
```