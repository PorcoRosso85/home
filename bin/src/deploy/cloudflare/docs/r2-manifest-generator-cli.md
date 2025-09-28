# R2 Connection Manifest Generator CLI

A robust command-line interface for generating environment-specific R2 connection manifests for Cloudflare R2 buckets. This tool provides comprehensive validation, error handling, and integration with SOPS encrypted secrets.

## Overview

The R2 Connection Manifest Generator CLI creates standardized manifest files that contain all necessary configuration for connecting to Cloudflare R2 buckets across different environments (development, staging, production). These manifests are essential for:

- S3-compatible client configuration
- Cloudflare Workers binding setup
- Multi-environment deployment management
- Secure credential handling

## Quick Start

```bash
# Basic usage - generate development environment manifest
nix run .#r2:gen-manifest -- dev

# Preview production configuration without writing files
nix run .#r2:gen-manifest -- -preview prod

# Generate with template data for testing
nix run .#r2:gen-manifest -- -template dev

# List all supported environments
nix run .#r2:envs
```

## Installation & Prerequisites

### Using Nix (Recommended)

```bash
# Enter development environment
nix develop

# Use directly via Nix
nix run .#gen-connection-manifest -- --env dev

# Use via Just commands
nix run .#r2:gen-manifest -- dev
```

### Manual Setup

For encrypted secrets mode (production use):
- SOPS configuration (`.sops.yaml`)
- Environment-specific secrets (`secrets/r2.<env>.yaml`)
- Age encryption key (`~/.config/sops/age/keys.txt`)

For template mode (testing):
- No prerequisites required

## Command Reference

### Core Commands

#### Generate Manifest
```bash
gen-connection-manifest --env <environment>
```

Generate an R2 connection manifest for the specified environment.

**Options:**
- `--env <ENV>` - Target environment (dev|stg|prod) [REQUIRED]
- `--output <PATH>` - Output directory (default: ./manifests)
- `--dry-run` - Preview generation without writing files
- `--verbose` - Enable detailed logging
- `--quiet` - Suppress non-error output
- `--force` - Overwrite existing manifest files
- `--use-template` - Use template data instead of encrypted secrets

**Examples:**
```bash
# Basic generation
gen-connection-manifest --env dev

# Custom output with verbose logging
gen-connection-manifest --env prod --output ./config/r2/ --verbose

# Preview without writing files
gen-connection-manifest --env stg --dry-run --verbose

# Force overwrite existing files
gen-connection-manifest --env prod --force

# Test with template data
gen-connection-manifest --env dev --use-template --dry-run
```

#### List Environments
```bash
gen-connection-manifest --list-environments
```

Display all supported environments and their configuration status.

#### Help
```bash
gen-connection-manifest --help
```

Show comprehensive help information with examples and prerequisites.

### Just Commands

The CLI is integrated with Just for convenient workflows:

```bash
# Generate manifest for specific environment
nix run .#r2:gen-manifest -- <env>

# Preview manifest without writing
nix run .#r2:gen-manifest -- -preview <env>

# Generate with template data
nix run .#r2:gen-manifest -- -template <env>

# List supported environments
nix run .#r2:envs
```

## Configuration

### Environment Secrets

Each environment requires a secrets file in the `secrets/` directory:

```
secrets/
├── r2.dev.yaml     # Development configuration
├── r2.stg.yaml     # Staging configuration
└── r2.prod.yaml    # Production configuration
```

#### Secret File Format

```yaml
# Cloudflare Account ID (required)
cf_account_id: your-account-id-here

# R2 bucket names (comma-separated for multiple buckets)
r2_buckets: user-uploads,static-assets

# S3 API credentials (optional - for S3-compatible access)
r2_access_key_id: your-access-key-here
r2_secret_access_key: your-secret-key-here
```

### SOPS Encryption

All secret files are encrypted using SOPS with Age encryption:

```bash
# Initialize secrets system
nix run .#secrets-init

# Edit environment secrets
nix run .#secrets-edit secrets/r2.dev.yaml
```

## Output Format

Generated manifests follow the R2 Connection Manifest Schema:

```json
{
  "account_id": "1234567890abcdef1234567890abcdef",
  "endpoint": "https://1234567890abcdef1234567890abcdef.r2.cloudflarestorage.com",
  "region": "auto",
  "buckets": [
    {
      "name": "user-uploads",
      "public": false
    },
    {
      "name": "static-assets",
      "public": true,
      "cors_origins": ["https://*.example.com"]
    }
  ],
  "connection_mode": "workers-binding",
  "credentials": {
    "access_key_id": "...",
    "secret_access_key": "..."
  },
  "meta": {
    "environment": "dev",
    "version": "1.0.0",
    "created_at": "2025-01-15T10:00:00Z",
    "description": "Development environment R2 configuration"
  }
}
```

### File Naming

Manifests are saved with the pattern: `r2.<environment>.json`

Examples:
- `r2.dev.json`
- `r2.stg.json`
- `r2.prod.json`

## Features

### Environment Validation
- Validates environment names against supported list (dev, stg, prod)
- Checks for required secret files
- Verifies SOPS encryption capability

### Comprehensive Error Handling
- Clear error messages with suggested solutions
- Validates prerequisites before execution
- Proper exit codes for CI/CD integration

### Security Features
- SOPS integration for encrypted secrets
- Template mode for safe testing
- No plaintext secrets in output (optional credentials)
- Age encryption key management

### User Experience
- Progress indicators for long operations
- Verbose and quiet modes
- Dry-run mode for safe previewing
- Help system with examples

### Integration Points
- JSON Schema validation
- External manifest validator integration
- Nix flake apps
- Just command workflows

## Error Codes

| Code | Description |
|------|-------------|
| 0    | Success |
| 1    | Invalid arguments or environment |
| 2    | Missing prerequisites (secrets, keys) |
| 3    | Validation failed |
| 4    | I/O error (file operations) |
| 5    | External command failed (SOPS, validation) |

## Troubleshooting

### Common Issues

#### "Node.js not found"
**Solution:** Use Nix development environment
```bash
nix develop -c gen-connection-manifest --env dev
```

#### "Missing prerequisites"
**Solution:** Initialize secrets system
```bash
nix run .#secrets-init
cp secrets/r2.yaml.example secrets/r2.dev.yaml
nix run .#secrets-edit secrets/r2.dev.yaml
```

#### "Environment not supported"
**Solution:** Use supported environments
```bash
gen-connection-manifest --list-environments
```

#### "Validation failed"
**Solution:** Check manifest schema compliance
```bash
./scripts/validate-r2-manifest.sh ./manifests/r2.dev.json
```

### Debug Mode

Enable verbose logging for detailed troubleshooting:
```bash
gen-connection-manifest --env dev --verbose
```

## Development

### Testing

Run the CLI test suite:
```bash
./test-cli.sh
```

### Integration Testing

Test with template data:
```bash
gen-connection-manifest --env dev --use-template --dry-run --verbose
```

### Validation

Validate generated manifests:
```bash
./scripts/validate-r2-manifest.sh ./manifests/r2.dev.json
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Generate R2 manifest
  run: |
    nix develop -c gen-connection-manifest --env ${{ matrix.environment }}

- name: Validate manifest
  run: |
    nix develop -c ./scripts/validate-r2-manifest.sh ./manifests/r2.${{ matrix.environment }}.json
```

### Application Configuration

```javascript
// Load environment-specific R2 configuration
import manifest from './manifests/r2.prod.json';

const r2Client = new S3Client({
  endpoint: manifest.endpoint,
  region: manifest.region,
  credentials: manifest.credentials
});
```

### Infrastructure as Code

```typescript
// Use manifest in Pulumi/Terraform
import * as r2Manifest from './manifests/r2.prod.json';

const buckets = r2Manifest.buckets.map(bucket =>
  new cloudflare.R2Bucket(bucket.name, {
    accountId: r2Manifest.account_id,
    name: bucket.name
  })
);
```

## Security Considerations

1. **Secret Management**: All production secrets are encrypted with SOPS
2. **Template Mode**: Use only for testing, never in production
3. **File Permissions**: Ensure manifest files have appropriate permissions
4. **Backup**: Generated manifests include backup of existing files
5. **Validation**: Always validate manifests before deployment

## Support

For issues and feature requests, refer to the project repository or documentation.
