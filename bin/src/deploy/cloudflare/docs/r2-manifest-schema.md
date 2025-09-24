# R2 Connection Manifest Schema

This document describes the R2 Connection Manifest schema used for environment-specific R2 bucket configuration.

## Overview

The R2 Connection Manifest provides a standardized format for defining R2 bucket configurations across different environments (dev, staging, production). It supports both Cloudflare Workers binding mode and S3-compatible API access.

## Files Created

### TypeScript Interface
- **Location**: `types/r2-manifest.ts`
- **Purpose**: Provides TypeScript type definitions for the manifest structure
- **Features**:
  - Complete type definitions for all manifest fields
  - Type guards and validation utilities
  - Helper functions for endpoint generation and bucket name validation

### JSON Schema
- **Location**: `schemas/r2-manifest.json`
- **Purpose**: JSON Schema for validation and documentation
- **Standards**: Compliant with JSON Schema Draft 2020-12
- **Features**:
  - Complete validation rules for all fields
  - Pattern matching for account IDs, endpoints, and bucket names
  - Conditional validation (credentials required for s3-api/hybrid modes)

### Example Manifests
- **Dev Example**: `examples/r2.dev.json.example`
  - Uses workers-binding mode (no credentials required)
  - Includes CORS origins for local development
  - Contains 3 buckets for different use cases

- **Production Example**: `examples/r2.prod.json.example`
  - Uses hybrid mode (Workers + S3 API)
  - Includes credentials configuration
  - Contains 4 buckets including backups and logs

### Validation Script
- **Location**: `scripts/validate-r2-manifest.sh`
- **Purpose**: Shell script for validating manifest files
- **Usage**: `./scripts/validate-r2-manifest.sh <manifest-file>...`

## Manifest Structure

```typescript
interface R2ConnectionManifest {
  account_id: string;           // Cloudflare Account ID
  endpoint: string;             // S3-compatible endpoint URL
  region: R2Region;             // R2 region ('auto', 'eeur', etc.)
  buckets: R2BucketConfig[];    // Array of bucket configurations
  connection_mode: R2ConnectionMode; // 'workers-binding', 's3-api', 'hybrid'
  credentials?: R2Credentials;  // Optional S3 API credentials
  meta: R2ManifestMeta;         // Metadata about the manifest
}
```

### Connection Modes

1. **workers-binding**: Uses Cloudflare Workers R2 binding (no credentials needed)
2. **s3-api**: Uses S3-compatible API (requires credentials)
3. **hybrid**: Supports both Workers binding and S3 API access

### Bucket Configuration

```typescript
interface R2BucketConfig {
  name: string;                 // Bucket name (S3 naming rules)
  public?: boolean;             // Whether bucket is publicly accessible
  custom_domain?: string;       // Custom domain for public access
  cors_origins?: string[];      // Allowed CORS origins
}
```

### Credentials (S3 API)

```typescript
interface R2Credentials {
  access_key_id: string;        // R2 Access Key ID
  secret_access_key: string;    // R2 Secret Access Key
  session_token?: string;       // Optional session token
}
```

## Validation Rules

1. **Account ID**: Must be 32-character hexadecimal string
2. **Endpoint**: Must follow `https://{account_id}.r2.cloudflarestorage.com` format
3. **Region**: Must be one of: auto, eeur, enam, apac, weur, wnam
4. **Bucket Names**: Must follow S3 naming conventions:
   - 3-63 characters long
   - Start and end with lowercase letter or number
   - Can contain lowercase letters, numbers, hyphens, and dots
   - Cannot contain consecutive dots
   - Cannot be an IP address format

5. **Connection Mode Dependencies**:
   - `s3-api` and `hybrid` modes require credentials
   - `workers-binding` mode doesn't require credentials

6. **Version**: Must follow semantic versioning (x.y.z)

## Usage Examples

### TypeScript Usage

```typescript
import { R2ConnectionManifest, isR2ConnectionManifest, generateR2Endpoint } from './types/r2-manifest';

// Load and validate manifest
const manifest: R2ConnectionManifest = JSON.parse(manifestJson);
if (!isR2ConnectionManifest(manifest)) {
  throw new Error('Invalid manifest structure');
}

// Generate endpoint from account ID
const endpoint = generateR2Endpoint('your-account-id');
```

### Validation

```bash
# Validate single manifest
./scripts/validate-r2-manifest.sh examples/r2.dev.json.example

# Validate multiple manifests
./scripts/validate-r2-manifest.sh out/r2.*.json
```

### JSON Schema Validation

The JSON schema can be used with any JSON Schema validator:

```bash
# Using ajv-cli (if available)
ajv validate -s schemas/r2-manifest.json -d examples/r2.dev.json.example
```

## File Naming Convention

Manifest files should follow the pattern: `r2.<environment>.json`

Examples:
- `r2.dev.json`
- `r2.staging.json`
- `r2.prod.json`

This naming convention makes it easy to:
1. Identify environment-specific configurations
2. Use glob patterns for batch operations
3. Integrate with deployment scripts

## Integration with Deployment

The manifest schema is designed to integrate seamlessly with:

1. **Cloudflare Workers**: Binding configuration
2. **S3-compatible clients**: AWS SDK, boto3, etc.
3. **Infrastructure as Code**: Pulumi, Terraform
4. **CI/CD pipelines**: Automated validation and deployment

## Security Considerations

1. **Credentials**: Never commit credentials in plain text
2. **Validation**: Always validate manifests before deployment
3. **Access Control**: Restrict access to production manifests
4. **Encryption**: Use SOPS or similar for sensitive data

---

For more information about R2 and its capabilities, see the [Cloudflare R2 documentation](https://developers.cloudflare.com/r2/).