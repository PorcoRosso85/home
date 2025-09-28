# 🌍 Environment Management Guide

Complete guide for managing multiple environments (dev, staging, production) in the R2 Connection Management System.

## 🎯 Environment Strategy

### Environment Types

**🧪 Development (dev)**
- **Purpose**: Local development and testing
- **Security**: Relaxed for developer productivity
- **R2 Mode**: Miniflare simulation (recommended)
- **Credentials**: Separate dev credentials or Miniflare

**🔬 Staging (stg)**
- **Purpose**: Pre-production testing and validation
- **Security**: Production-like but with relaxed CORS
- **R2 Mode**: Real R2 buckets with staging prefix
- **Credentials**: Separate staging credentials

**🚀 Production (prod)**
- **Purpose**: Live production environment
- **Security**: Maximum security settings
- **R2 Mode**: Real R2 buckets
- **Credentials**: Production-only credentials

## 📁 Environment Configuration Structure

### File Organization

```
secrets/
├── r2.yaml              # Default (usually production)
├── r2-dev.yaml          # Development environment
├── r2-stg.yaml          # Staging environment
└── r2-prod.yaml         # Production environment (explicit)

generated/
├── r2-connection-manifest-dev.json
├── r2-connection-manifest-stg.json
└── r2-connection-manifest-prod.json

wrangler.jsonc           # Current active configuration
```

### Environment Naming Convention

**Bucket Naming:**
```yaml
# Development
r2_buckets:
  - name: "dev-my-app-storage"
  - name: "dev-my-app-assets"

# Staging
r2_buckets:
  - name: "staging-my-app-storage"
  - name: "staging-my-app-assets"

# Production
r2_buckets:
  - name: "my-app-storage"
  - name: "my-app-assets"
```

**Worker Naming:**
```jsonc
// Development
{
  "name": "my-app-dev",
  "account_id": "dev-account-id"
}

// Staging
{
  "name": "my-app-staging",
  "account_id": "staging-account-id"
}

// Production
{
  "name": "my-app",
  "account_id": "prod-account-id"
}
```

## ⚙️ Environment Setup

### 1. Development Environment Setup

**Create development configuration:**
```bash
# Copy base template
cp r2.yaml.example secrets/r2-dev.yaml

# Edit development configuration
nix run .#secrets-edit secrets/r2-dev.yaml
```

**Development configuration template:**
```yaml
# Development Environment Configuration
cf_account_id: "dev-account-id-or-use-miniflare"
environment: "dev"
description: "Development environment for local testing"

r2_buckets:
  - name: "dev-my-app-storage"
    purpose: "development-storage"
    public_access: false
    cors_origins:
      - "http://localhost:3000"
      - "http://localhost:8787"
      - "http://127.0.0.1:3000"

  - name: "dev-my-app-assets"
    purpose: "development-assets"
    public_access: true
    cors_origins:
      - "http://localhost:3000"
      - "http://localhost:8787"

# Development can use Miniflare (no real credentials needed)
r2_credentials:
  access_key_id: "miniflare-dev-key"
  secret_access_key: "miniflare-dev-secret"

security:
  require_auth: false          # Relaxed for development
  rate_limiting: false
  encryption_at_rest: true
  access_control: "relaxed"

monitoring:
  enable_metrics: false        # Disable for local dev
  log_level: "debug"
```

**Generate development configuration:**
```bash
nix run .#r2:gen-config -- dev
nix run .#r2:validate -- dev
```

### 2. Staging Environment Setup

**Create staging configuration:**
```bash
cp secrets/r2-dev.yaml secrets/r2-stg.yaml
nix run .#secrets-edit secrets/r2-stg.yaml
```

**Staging configuration template:**
```yaml
# Staging Environment Configuration
cf_account_id: "staging-account-id"
environment: "stg"
description: "Staging environment for pre-production testing"

r2_buckets:
  - name: "staging-my-app-storage"
    purpose: "staging-storage"
    public_access: false
    cors_origins:
      - "https://staging.myapp.com"
      - "https://staging-api.myapp.com"

  - name: "staging-my-app-assets"
    purpose: "staging-assets"
    public_access: true
    custom_domain: "staging-assets.myapp.com"
    cors_origins:
      - "https://staging.myapp.com"

# Real R2 credentials for staging
r2_credentials:
  access_key_id: "staging-r2-access-key"
  secret_access_key: "staging-r2-secret-key"

security:
  require_auth: true
  rate_limiting: false         # Relaxed for testing
  encryption_at_rest: true
  access_control: "standard"

monitoring:
  enable_metrics: true
  log_level: "info"
  alerts:
    error_threshold: 50        # Lower threshold for staging
    latency_threshold: 3000
```

**Generate staging configuration:**
```bash
nix run .#r2:gen-config -- stg
nix run .#r2:validate -- stg
```

### 3. Production Environment Setup

**Create production configuration:**
```bash
cp secrets/r2-stg.yaml secrets/r2-prod.yaml
nix run .#secrets-edit secrets/r2-prod.yaml
```

**Production configuration template:**
```yaml
# Production Environment Configuration
cf_account_id: "production-account-id"
environment: "prod"
description: "Production environment with maximum security"

r2_buckets:
  - name: "my-app-storage"
    purpose: "production-storage"
    public_access: false
    cors_origins:
      - "https://myapp.com"
      - "https://www.myapp.com"
      - "https://api.myapp.com"

  - name: "my-app-assets"
    purpose: "production-assets"
    public_access: true
    custom_domain: "assets.myapp.com"
    cors_origins:
      - "https://myapp.com"
      - "https://www.myapp.com"

  - name: "my-app-backups"
    purpose: "production-backups"
    public_access: false
    # No CORS for backup bucket

# Production R2 credentials
r2_credentials:
  access_key_id: "production-r2-access-key"
  secret_access_key: "production-r2-secret-key"

security:
  require_auth: true           # Strict security
  rate_limiting: true
  encryption_at_rest: true
  access_control: "strict"

monitoring:
  enable_metrics: true
  log_level: "warn"           # Less verbose in production
  alerts:
    error_threshold: 100
    latency_threshold: 5000

deployment:
  mode: "production"
  environment_variables:
    - name: "NODE_ENV"
      value: "production"
    - name: "LOG_LEVEL"
      value: "warn"
```

**Generate production configuration:**
```bash
nix run .#r2:gen-config -- prod
nix run .#r2:validate -- prod
```

## 🔄 Environment Switching

### Manual Environment Switching

```bash
# Switch to development
nix run .#r2:gen-config -- dev
# Now wrangler.jsonc is configured for dev

# Switch to staging
nix run .#r2:gen-config -- stg
# Now wrangler.jsonc is configured for staging

# Switch to production
nix run .#r2:gen-config -- prod
# Now wrangler.jsonc is configured for production
```

### Environment-Specific Deployment

**Using Wrangler environments:**
```jsonc
// wrangler.jsonc with multiple environments
{
  "name": "my-app",
  "main": "src/worker.ts",
  "compatibility_date": "2024-09-01",

  // Default environment (dev)
  "account_id": "dev-account-id",
  "r2_buckets": [
    {"binding": "STORAGE", "bucket_name": "dev-my-app-storage"}
  ],

  // Environment overrides
  "env": {
    "staging": {
      "account_id": "staging-account-id",
      "r2_buckets": [
        {"binding": "STORAGE", "bucket_name": "staging-my-app-storage"}
      ]
    },
    "production": {
      "account_id": "production-account-id",
      "r2_buckets": [
        {"binding": "STORAGE", "bucket_name": "my-app-storage"}
      ]
    }
  }
}
```

**Deploy to specific environments:**
```bash
# Deploy to development (default)
wrangler deploy

# Deploy to staging
wrangler deploy --env staging

# Deploy to production
wrangler deploy --env production
```

## 🧪 Environment Testing

### Development Testing

```bash
# Test local development setup
nix run .#r2-dev-workflow -- test dev

# Start local development server
wrangler dev --local

# Test with local server
curl -X POST http://localhost:8787/api/upload-test
```

### Staging Testing

```bash
# Validate staging configuration
nix run .#r2:validate -- stg

# Deploy to staging
nix run .#r2-dev-workflow -- deploy-prep stg
wrangler deploy --env staging

# Test staging deployment
curl -X POST https://my-app-staging.workers.dev/api/upload-test
```

### Production Testing

```bash
# Validate production configuration (no deployment)
nix run .#r2:validate -- prod

# Prepare for production deployment
nix run .#r2-dev-workflow -- deploy-prep prod

# Deploy to production (when ready)
wrangler deploy --env production

# Test production deployment
curl -X GET https://my-app.workers.dev/health
```

## 🔒 Environment Security

### Security by Environment

**Development:**
- ✅ Local testing with Miniflare (no real credentials)
- ✅ Relaxed CORS for local development
- ✅ Debug logging enabled
- ❌ No rate limiting
- ❌ Authentication optional

**Staging:**
- ✅ Real R2 credentials (staging-specific)
- ✅ Production-like security settings
- ✅ Monitoring enabled
- ⚠️ Relaxed rate limiting for testing
- ✅ Authentication required

**Production:**
- ✅ Maximum security settings
- ✅ Strict CORS policies
- ✅ Full monitoring and alerting
- ✅ Rate limiting enabled
- ✅ Encryption at rest
- ✅ Access control enforced

### Credential Isolation

**Separate credentials per environment:**
```yaml
# Development - Use Miniflare or separate dev credentials
r2_credentials:
  access_key_id: "dev-specific-key"
  secret_access_key: "dev-specific-secret"

# Staging - Dedicated staging credentials
r2_credentials:
  access_key_id: "staging-specific-key"
  secret_access_key: "staging-specific-secret"

# Production - Production-only credentials
r2_credentials:
  access_key_id: "production-only-key"
  secret_access_key: "production-only-secret"
```

**Cloudflare account separation:**
- Development: Personal or dev Cloudflare account
- Staging: Shared staging Cloudflare account
- Production: Production Cloudflare account

## 📊 Environment Monitoring

### Environment-Specific Monitoring

**Development:**
```typescript
// Development Worker - Verbose logging
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    console.log('DEV: Request received:', {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers)
    });

    try {
      const result = await handleRequest(request, env);
      console.log('DEV: Request successful');
      return result;
    } catch (error) {
      console.error('DEV: Request failed:', error);
      throw error;
    }
  }
};
```

**Production:**
```typescript
// Production Worker - Minimal logging with metrics
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const startTime = Date.now();

    try {
      const result = await handleRequest(request, env);

      // Log metrics only
      env.ANALYTICS?.writeDataPoint({
        timestamp: Date.now(),
        duration: Date.now() - startTime,
        status: 'success',
        environment: 'production'
      });

      return result;
    } catch (error) {
      // Log errors only
      console.error('Request failed:', error.message);

      env.ANALYTICS?.writeDataPoint({
        timestamp: Date.now(),
        duration: Date.now() - startTime,
        status: 'error',
        environment: 'production',
        error: error.message
      });

      throw error;
    }
  }
};
```

### Environment Health Checks

```typescript
// Environment-aware health check
app.get('/health', async (c) => {
  const environment = c.env.ENVIRONMENT || 'unknown';

  const health = {
    status: 'healthy',
    environment,
    timestamp: new Date().toISOString(),
    checks: {}
  };

  try {
    // Test R2 connectivity
    await c.env.STORAGE.head('health-check-file');
    health.checks.r2 = 'ok';
  } catch (error) {
    health.checks.r2 = 'failed';
    health.status = 'unhealthy';
  }

  // Environment-specific checks
  if (environment === 'production') {
    // Additional production checks
    health.checks.backup_bucket = await testBackupBucket(c.env);
    health.checks.monitoring = await testMonitoring(c.env);
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  return c.json(health, statusCode);
});
```

## 🔄 Environment Workflows

### Development Workflow

```bash
# Daily development routine
cd my-r2-project

# Enter development environment
nix develop

# Start with fresh configuration
nix run .#r2:gen-config -- dev

# Test locally
nix run .#r2-dev-workflow -- test dev

# Start development server
wrangler dev --local

# Make changes, test, repeat...

# Commit changes
git add .
git commit -m "Add new feature"
```

### Staging Deployment Workflow

```bash
# Prepare staging deployment
nix run .#r2-dev-workflow -- deploy-prep stg

# Deploy to staging
wrangler deploy --env staging

# Test staging deployment
curl -X POST https://my-app-staging.workers.dev/api/test

# Monitor staging logs
wrangler tail --env staging

# If tests pass, prepare for production
```

### Production Deployment Workflow

```bash
# Final validation
nix run .#r2:validate -- -all

# Backup current production config
nix run .#r2-backup-config

# Prepare production deployment
nix run .#r2-dev-workflow -- deploy-prep prod

# Deploy to production
wrangler deploy --env production

# Monitor production deployment
wrangler tail --env production --filter error

# Verify health
curl -X GET https://my-app.workers.dev/health
```

## 🚨 Environment Troubleshooting

### Common Environment Issues

**Wrong environment deployed:**
```bash
# Check current configuration
cat wrangler.jsonc | jq '.account_id'

# Regenerate correct environment
nix run .#r2:gen-config -- prod

# Redeploy
wrangler deploy --env production
```

**Environment configuration mismatch:**
```bash
# Compare environment configurations
nix run .#r2-diff-configs -- dev prod

# Check for differences and update accordingly
nix run .#secrets-edit secrets/r2-prod.yaml
```

**Missing environment files:**
```bash
# List available environments
nix run .#r2:envs

# Create missing environment
cp secrets/r2.yaml secrets/r2-missing.yaml
nix run .#secrets-edit secrets/r2-missing.yaml
```

### Environment Validation

```bash
# Validate specific environment
nix run .#r2:validate -- stg

# Validate all environments
nix run .#r2:validate -- -all

# Check for environment-specific issues
nix run .#r2:status -- stg
```

## 📋 Environment Checklist

### Pre-Deployment Checklist

**Development:**
- [ ] Local testing with Miniflare works
- [ ] All R2 operations function correctly
- [ ] Code changes tested locally
- [ ] No hardcoded credentials in code

**Staging:**
- [ ] Staging configuration validated
- [ ] Staging buckets created in Cloudflare
- [ ] Staging credentials configured
- [ ] CORS origins set for staging domains
- [ ] Deployment successful
- [ ] All features tested in staging

**Production:**
- [ ] Production configuration validated
- [ ] Production buckets created
- [ ] Production credentials secured
- [ ] CORS limited to production domains
- [ ] Security settings at maximum
- [ ] Monitoring and alerting configured
- [ ] Backup procedures in place
- [ ] Team notified of deployment

### Post-Deployment Checklist

- [ ] Health check endpoint responds
- [ ] All R2 operations work
- [ ] Logs show no errors
- [ ] Monitoring metrics look normal
- [ ] Performance meets expectations
- [ ] Security scans pass

## 📚 Related Documentation

- **[Production Setup Guide](production-setup.md)** - Detailed production environment setup
- **[Security Guide](security-guide.md)** - Environment-specific security
- **[Command Reference](command-reference.md)** - Environment management commands
- **[Troubleshooting Guide](troubleshooting.md)** - Environment-specific issues
