# 📖 Migration Guide

Complete guide for migrating from old R2 connection systems to the new comprehensive R2 Connection Management System.

## 🎯 Migration Overview

This guide covers migration from:
- **Legacy Wrangler configurations** (manual wrangler.toml/jsonc)
- **Basic R2 setups** (without encryption or environment management)
- **Custom R2 integration scripts** (ad-hoc solutions)
- **AWS S3 implementations** (moving to R2)

### What You'll Gain

**🔒 Enhanced Security:**
- SOPS-encrypted secrets with Age encryption
- Automatic plaintext secret detection
- Comprehensive security policies

**🌍 Multi-Environment Support:**
- Separate configurations for dev/staging/prod
- Environment-specific credential management
- Easy environment switching

**📋 Schema Validation:**
- TypeScript-first configuration
- JSON Schema validation
- Comprehensive error checking

**🧪 Better Development Experience:**
- Miniflare local testing
- Comprehensive command-line tools
- Automated configuration generation

## 📋 Pre-Migration Assessment

### 1. Inventory Current Setup

**Document your current configuration:**
```bash
# List current R2 buckets
wrangler r2 bucket list

# Backup current wrangler configuration
cp wrangler.toml wrangler.toml.backup.$(date +%Y%m%d)
cp wrangler.jsonc wrangler.jsonc.backup.$(date +%Y%m%d) 2>/dev/null || true

# Document current environment variables
env | grep -E "(CLOUDFLARE|R2|WRANGLER)" > current-env.backup
```

**Identify credentials and secrets:**
```bash
# Find files containing potential secrets
find . -type f -name "*.env*" -o -name "*.toml" -o -name "*.json" | \
  xargs grep -l -E "(AKIA|sk_|pk_|token|secret|key)" 2>/dev/null

# Check for hardcoded credentials in code
grep -r -E "(AKIA[A-Z0-9]{16}|sk_[a-zA-Z0-9]+)" src/ 2>/dev/null || true
```

### 2. Plan Migration Strategy

**Choose migration approach:**

**🚀 Big Bang Migration** (Recommended for small projects):
- Migrate everything at once
- Shorter migration period
- Requires careful planning

**🔄 Gradual Migration** (Recommended for large projects):
- Migrate environment by environment
- Start with development, then staging, then production
- Lower risk but longer timeline

**📱 Parallel Running** (For critical systems):
- Run old and new systems in parallel
- Gradual traffic migration
- Maximum safety but highest complexity

## 🏗️ Step-by-Step Migration

### Phase 1: Setup New System

#### 1.1 Initialize New R2 System

```bash
# Clone or setup new R2 system
cd /path/to/new-r2-system

# Enter development environment
nix develop

# Initialize the system
nix run .#r2-dev-workflow -- setup
```

#### 1.2 Initialize Secret Management

```bash
# Setup SOPS encryption
nix run .#secrets-init

# This creates:
# - Age encryption key in ~/.config/sops/age/keys.txt
# - SOPS configuration in .sops.yaml

# Backup your Age key immediately
cp ~/.config/sops/age/keys.txt ~/secure-backup/age-key-$(date +%Y%m%d).txt
```

### Phase 2: Migrate Configuration

#### 2.1 Extract Current Configuration

**From wrangler.toml:**
```bash
# Extract key information
echo "=== Current Wrangler Configuration ===" > migration-data.txt
echo "Account ID: $(grep 'account_id' wrangler.toml | cut -d'"' -f2)" >> migration-data.txt
echo "R2 Buckets:" >> migration-data.txt
grep -A 10 '\[\[r2_buckets\]\]' wrangler.toml >> migration-data.txt
```

**From environment variables:**
```bash
# Document current environment variables
echo "=== Environment Variables ===" >> migration-data.txt
env | grep -E "(CLOUDFLARE|R2)" >> migration-data.txt
```

#### 2.2 Create New Configuration

```bash
# Start with the example template
cp r2.yaml.example secrets/r2.yaml

# Edit with your actual values
nix run .#secrets-edit secrets/r2.yaml
```

**Configuration template with migration notes:**
```yaml
# === MIGRATION FROM OLD SYSTEM ===
# Fill in these values from your migration-data.txt

# From wrangler.toml account_id
cf_account_id: "your-32-character-account-id"

# Environment configuration
environment: "prod"  # or "dev", "stg"
description: "Migrated from legacy R2 setup"

# === R2 BUCKETS ===
# From wrangler.toml [[r2_buckets]] sections
r2_buckets:
  - name: "legacy-bucket-name-1"
    purpose: "main-storage"       # Add purpose description
    public_access: false          # Set based on current usage
    cors_origins:                 # Add if using CORS
      - "https://yourdomain.com"

  - name: "legacy-bucket-name-2"
    purpose: "static-assets"
    public_access: true           # If currently public
    custom_domain: "assets.yourdomain.com"  # If using custom domain

# === R2 CREDENTIALS ===
# From Cloudflare Dashboard → R2 → API tokens
r2_credentials:
  access_key_id: "your-r2-access-key-id"
  secret_access_key: "your-r2-secret-access-key"

# === SECURITY CONFIGURATION ===
# New features not in old system
security:
  require_auth: true
  rate_limiting: true
  encryption_at_rest: true
  access_control: "strict"

# === MONITORING ===
# Enhanced monitoring capabilities
monitoring:
  enable_metrics: true
  log_level: "info"
  alerts:
    error_threshold: 100
    latency_threshold: 5000
```

#### 2.3 Generate New Configurations

```bash
# Generate wrangler.jsonc for each environment
nix run .#r2:gen-config -- dev
nix run .#r2:gen-config -- stg
nix run .#r2:gen-config -- prod

# Generate connection manifests
nix run .#r2:gen-manifest -- dev
nix run .#r2:gen-manifest -- stg
nix run .#r2:gen-manifest -- prod

# Validate all configurations
nix run .#r2:validate -- -all
```

### Phase 3: Code Migration

#### 3.1 Update Worker Code

**If using Workers binding (recommended):**

**Old code:**
```typescript
// Old R2 access
export default {
  async fetch(request: Request, env: any): Promise<Response> {
    // Direct bucket access without validation
    const result = await env.MY_BUCKET.put('file.txt', 'data');
    return new Response('OK');
  }
};
```

**New code:**
```typescript
// New R2 access with enhanced features
interface Env {
  R2_BUCKET: R2Bucket;
  // Other bindings...
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      // Enhanced R2 operations with error handling
      const result = await env.R2_BUCKET.put('file.txt', 'data', {
        customMetadata: {
          uploadedAt: new Date().toISOString(),
          environment: 'production'
        }
      });

      return new Response(JSON.stringify({
        success: true,
        etag: result.etag
      }));

    } catch (error) {
      console.error('R2 operation failed:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }
};
```

#### 3.2 Migrate AWS SDK Code

**If migrating from AWS S3 to R2:**

**Old S3 code:**
```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

const s3Client = new S3Client({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});
```

**New R2 code:**
```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

// Load R2 configuration from generated manifest
function loadR2Config(environment = 'prod') {
  const manifest = JSON.parse(
    readFileSync(`generated/r2-connection-manifest-${environment}.json`, 'utf8')
  );

  return new S3Client({
    region: manifest.region,           // 'auto' for R2
    endpoint: manifest.endpoint,       // R2 endpoint
    credentials: manifest.credentials, // R2 credentials
    forcePathStyle: true              // Required for R2
  });
}

const r2Client = loadR2Config();
```

#### 3.3 Update Environment Configuration

**Replace environment variables:**

**Old .env:**
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=my-bucket
```

**New approach (no .env file needed):**
```bash
# Configuration is loaded from generated manifests
# Credentials are encrypted in secrets/r2.yaml
# Environment-specific settings in generated configs

# For local development
nix run .#r2-dev-workflow -- test dev

# For production
nix run .#r2-dev-workflow -- deploy-prep prod
```

### Phase 4: Testing Migration

#### 4.1 Test Local Development

```bash
# Test new system locally with Miniflare
nix run .#r2-dev-workflow -- test dev

# Start local development server
wrangler dev --local

# Verify R2 operations work
curl -X POST http://localhost:8787/api/test-upload
```

#### 4.2 Test Staging Environment

```bash
# Deploy to staging first
nix run .#r2-dev-workflow -- deploy-prep stg

# Deploy staging Worker
wrangler deploy --env staging

# Test staging functionality
curl -X POST https://your-worker-staging.workers.dev/api/test
```

#### 4.3 Validate Production Configuration

```bash
# Validate production config without deploying
nix run .#r2:validate -- prod

# Check for any issues
nix run .#secrets-check

# Run comprehensive validation
nix run .#r2:validate -- -all
```

### Phase 5: Production Migration

#### 5.1 Pre-Migration Checklist

```bash
# ✅ Backup current system
cp wrangler.toml wrangler.toml.pre-migration
cp -r .wrangler .wrangler.pre-migration 2>/dev/null || true

# ✅ Test new system in staging
nix run .#r2-dev-workflow -- deploy-prep stg
wrangler deploy --env staging

# ✅ Validate production configuration
nix run .#r2:validate -- prod

# ✅ Ensure Age key is backed up
cp ~/.config/sops/age/keys.txt ~/backup/

# ✅ Coordinate with team
echo "Migration scheduled for $(date)"
```

#### 5.2 Execute Migration

**Option A: Big Bang Migration**
```bash
# 1. Deploy new production configuration
nix run .#r2-dev-workflow -- deploy-prep prod

# 2. Deploy to production
wrangler deploy

# 3. Test immediately
curl -X GET https://your-worker.workers.dev/health

# 4. Monitor logs
wrangler tail --format pretty
```

**Option B: Blue-Green Migration**
```bash
# 1. Deploy to new subdomain first
wrangler deploy --env migration-test

# 2. Test new deployment
curl -X GET https://your-worker-migration-test.workers.dev/health

# 3. Switch DNS/routing to new deployment
# (Implementation depends on your setup)

# 4. Monitor and verify
wrangler tail --format pretty
```

#### 5.3 Post-Migration Verification

```bash
# Verify all R2 operations work
curl -X POST https://your-worker.workers.dev/api/upload-test
curl -X GET https://your-worker.workers.dev/api/download-test
curl -X DELETE https://your-worker.workers.dev/api/delete-test

# Check logs for errors
wrangler tail --filter error --lines 100

# Verify metrics (if configured)
# Check Cloudflare Analytics dashboard
```

## 🔄 Environment-Specific Migrations

### Development Environment

```bash
# 1. Setup development environment
nix run .#secrets-edit secrets/r2-dev.yaml

# Configure for development:
r2_buckets:
  - name: "dev-my-bucket"          # Add dev prefix
    purpose: "development-testing"
    public_access: false
    cors_origins:
      - "http://localhost:3000"    # Local dev origins
      - "http://localhost:8787"

security:
  require_auth: false              # Relaxed for dev
  rate_limiting: false
  encryption_at_rest: true

# 2. Generate dev configuration
nix run .#r2:gen-config -- dev

# 3. Test locally
nix run .#r2-dev-workflow -- test dev
```

### Staging Environment

```bash
# 1. Setup staging environment
nix run .#secrets-edit secrets/r2-stg.yaml

# Configure for staging:
r2_buckets:
  - name: "staging-my-bucket"      # Add staging prefix
    purpose: "staging-testing"
    public_access: false
    cors_origins:
      - "https://staging.yourdomain.com"

security:
  require_auth: true
  rate_limiting: false             # Relaxed for testing
  encryption_at_rest: true

# 2. Generate staging configuration
nix run .#r2:gen-config -- stg

# 3. Deploy and test
wrangler deploy --env staging
```

### Production Environment

```bash
# 1. Setup production environment (most secure)
nix run .#secrets-edit secrets/r2-prod.yaml

# Configure for production:
r2_buckets:
  - name: "production-my-bucket"   # Production names
    purpose: "production-storage"
    public_access: false
    cors_origins:
      - "https://yourdomain.com"   # Only production domains

security:
  require_auth: true               # Strict security
  rate_limiting: true
  encryption_at_rest: true
  access_control: "strict"

# 2. Generate production configuration
nix run .#r2:gen-config -- prod

# 3. Validate before deployment
nix run .#r2:validate -- prod
```

## 🚨 Rollback Procedures

### If Migration Goes Wrong

#### Immediate Rollback

```bash
# 1. Restore old wrangler configuration
cp wrangler.toml.pre-migration wrangler.toml
cp wrangler.jsonc.backup.YYYYMMDD wrangler.jsonc 2>/dev/null || true

# 2. Redeploy old version
wrangler deploy

# 3. Verify old system works
curl -X GET https://your-worker.workers.dev/health
```

#### Partial Rollback (Environment-Specific)

```bash
# Rollback specific environment
wrangler deploy --env staging  # Deploy old staging config

# Keep other environments on new system
nix run .#r2-dev-workflow -- deploy-prep prod
wrangler deploy --env production
```

### Post-Rollback Analysis

```bash
# Collect error information
wrangler tail --filter error --lines 500 > migration-errors.log

# Check configuration differences
diff wrangler.toml.pre-migration wrangler.toml

# Review what went wrong
# Common issues:
# - Incorrect bucket names
# - Missing CORS configuration
# - Authentication problems
# - Network connectivity issues
```

## 📊 Migration Validation

### Functional Testing

```bash
# Test script for validating migration
#!/bin/bash
set -e

echo "=== Migration Validation ==="

# Test 1: Configuration validation
echo "Testing configuration..."
nix run .#r2:validate -- -all

# Test 2: Local development
echo "Testing local development..."
nix run .#r2-dev-workflow -- test dev

# Test 3: Basic R2 operations
echo "Testing R2 operations..."
curl -X POST https://your-worker.workers.dev/api/test-upload
curl -X GET https://your-worker.workers.dev/api/test-download
curl -X DELETE https://your-worker.workers.dev/api/test-delete

# Test 4: Security checks
echo "Testing security..."
nix run .#secrets-check

echo "✅ Migration validation complete"
```

### Performance Comparison

```bash
# Before migration metrics
echo "=== Pre-Migration Metrics ===" > migration-metrics.txt
curl -w "@curl-format.txt" -o /dev/null -s https://your-worker.workers.dev/api/test

# After migration metrics
echo "=== Post-Migration Metrics ===" >> migration-metrics.txt
curl -w "@curl-format.txt" -o /dev/null -s https://your-worker.workers.dev/api/test

# curl-format.txt:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_redirect:    %{time_redirect}\n
# time_starttransfer: %{time_starttransfer}\n
# ----------\n
# time_total:       %{time_total}\n
```

## 🧹 Post-Migration Cleanup

### Remove Old Files

```bash
# After successful migration (wait at least 1 week)

# Remove backup files
rm wrangler.toml.backup.*
rm wrangler.jsonc.backup.*
rm current-env.backup
rm migration-data.txt

# Remove old environment files
rm .env 2>/dev/null || true
rm .env.local 2>/dev/null || true
rm .env.production 2>/dev/null || true

# Clean up old wrangler cache
rm -rf .wrangler.pre-migration
```

### Update Documentation

```bash
# Update project README
# Document new commands and procedures

# Update deployment scripts
# Replace old wrangler commands with new just commands

# Update CI/CD pipelines
# Replace environment variables with new secret management
```

### Team Training

**Update team knowledge:**
- Document new commands (`just help`)
- Train on secret management (`just secrets:edit`)
- Share troubleshooting guide (`docs/troubleshooting.md`)
- Review security practices (`docs/security-guide.md`)

## 📈 Migration Benefits Realized

### Before vs. After Comparison

**Before Migration:**
```bash
# Manual configuration management
vim wrangler.toml

# Plaintext secrets in environment
export R2_ACCESS_KEY="..."

# No validation
wrangler deploy  # Hope it works

# Limited environments
# Copy/paste configuration
```

**After Migration:**
```bash
# Automated configuration generation
nix run .#r2:gen-config -- prod

# Encrypted secret management
nix run .#secrets-edit

# Comprehensive validation
nix run .#r2:validate -- -all

# Multi-environment support
nix run .#r2-dev-workflow -- deploy-prep prod
```

### Security Improvements

- ✅ **Encrypted secrets** with SOPS/Age
- ✅ **Plaintext detection** prevents credential leaks
- ✅ **Environment separation** with different credentials
- ✅ **Access control** with fine-grained permissions
- ✅ **Audit logging** for security monitoring

### Development Experience Improvements

- ✅ **Local testing** with Miniflare
- ✅ **Schema validation** catches errors early
- ✅ **Command-line tools** automate common tasks
- ✅ **Comprehensive documentation** reduces confusion
- ✅ **Troubleshooting guides** solve problems faster

## 🆘 Migration Support

### Common Migration Issues

1. **Credential Problems**: See [Troubleshooting Guide](troubleshooting.md#authentication--credentials-issues)
2. **Configuration Errors**: See [Troubleshooting Guide](troubleshooting.md#configuration-issues)
3. **CORS Issues**: See [Troubleshooting Guide](troubleshooting.md#cors-issues-in-production)
4. **Performance Issues**: See [Troubleshooting Guide](troubleshooting.md#performance-issues)

### Getting Help

If you encounter issues during migration:

1. **Check troubleshooting guide**: [docs/troubleshooting.md](troubleshooting.md)
2. **Run diagnostics**: `just status && just r2:validate-all`
3. **Review logs**: `wrangler tail --filter error`
4. **Check configuration**: `just secrets:check`

### Migration Checklist

```markdown
## Migration Checklist

### Pre-Migration
- [ ] Document current setup
- [ ] Backup current configuration
- [ ] Plan rollback strategy
- [ ] Coordinate with team

### Migration
- [ ] Setup new system
- [ ] Initialize secret management
- [ ] Migrate configuration
- [ ] Update code
- [ ] Test locally
- [ ] Test in staging
- [ ] Deploy to production

### Post-Migration
- [ ] Verify functionality
- [ ] Monitor for issues
- [ ] Update documentation
- [ ] Train team
- [ ] Clean up old files

### Validation
- [ ] All R2 operations work
- [ ] Security checks pass
- [ ] Performance is acceptable
- [ ] Team is trained
```

This migration guide provides a comprehensive path from legacy R2 setups to the new secure, validated, and maintainable R2 Connection Management System. Take your time with each phase and don't hesitate to rollback if issues arise.
