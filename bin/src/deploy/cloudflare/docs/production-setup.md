# 🚀 Production R2 Setup Guide

Complete guide for setting up real Cloudflare R2 connections for production deployment.

## 🎯 Prerequisites

Before starting, ensure you have:

- **Cloudflare Account**: Free or paid account with R2 enabled
- **R2 Subscription**: R2 must be enabled in your Cloudflare account
- **API Tokens**: Cloudflare API token with R2 permissions
- **R2 Credentials**: R2 access key ID and secret access key

## 🏗️ Cloudflare Account Setup

### 1. Enable R2 in Your Cloudflare Account

1. Log into [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2 Object Storage**
3. Accept the R2 terms and enable the service
4. Note your **Account ID** (visible in the right sidebar)

### 2. Create R2 Buckets

```bash
# Using Wrangler CLI
wrangler r2 bucket create my-production-bucket
wrangler r2 bucket create my-staging-bucket
wrangler r2 bucket create my-development-bucket

# Or use the Cloudflare Dashboard:
# R2 Object Storage → Create bucket
```

### 3. Generate R2 API Credentials

1. Go to **R2 Object Storage** → **Manage R2 API tokens**
2. Click **Create API token**
3. Configure permissions:
   - **Object Read**: For getting objects
   - **Object Write**: For putting/deleting objects
   - **Bucket Read**: For listing buckets
   - **Bucket Write**: For managing buckets (if needed)
4. Select specific buckets or allow all buckets
5. Save the **Access Key ID** and **Secret Access Key**

### 4. Generate Cloudflare API Token

1. Go to **My Profile** → **API Tokens**
2. Click **Create Token**
3. Use **Custom token** template
4. Configure permissions:
   - **Account**: `Cloudflare Workers:Edit`
   - **Zone Resources**: Include all zones or specific zones
5. Save the token for Wrangler authentication

## 🔐 Local Setup and Secret Management

### 1. Initialize Encrypted Secrets

```bash
# Initialize SOPS encryption
just secrets:init

# This creates:
# - Age encryption key in ~/.config/sops/age/keys.txt
# - SOPS configuration in .sops.yaml
```

### 2. Configure R2 Connection Details

```bash
# Copy the example configuration
cp r2.yaml.example secrets/r2.yaml

# Edit with your actual credentials
just secrets:edit secrets/r2.yaml
```

### 3. R2 Configuration Template

Edit your `secrets/r2.yaml` with your actual values:

```yaml
# R2 Connection Configuration
cf_account_id: "your-32-character-account-id"
environment: "prod"
description: "Production R2 configuration"

# R2 Buckets Configuration
r2_buckets:
  - name: "my-production-bucket"
    purpose: "main-storage"
    public_access: false
    cors_origins:
      - "https://yourdomain.com"
      - "https://www.yourdomain.com"

  - name: "my-static-assets"
    purpose: "static-files"
    public_access: true
    custom_domain: "assets.yourdomain.com"

# R2 API Credentials (for S3-compatible API)
r2_credentials:
  access_key_id: "your-r2-access-key-id"
  secret_access_key: "your-r2-secret-access-key"

# Security Configuration
security:
  require_auth: true
  rate_limiting: true
  encryption_at_rest: true
  access_control: "strict"

# Monitoring Configuration
monitoring:
  enable_metrics: true
  log_level: "info"
  alerts:
    error_threshold: 100
    latency_threshold: 5000

# Deployment Configuration
deployment:
  mode: "production"
  environment_variables:
    - name: "R2_BUCKET_PREFIX"
      value: "prod"
    - name: "CORS_ORIGIN"
      value: "https://yourdomain.com"
```

## ⚙️ Generate Production Configuration

### 1. Generate Wrangler Configuration

```bash
# Generate wrangler.jsonc for production
just r2:gen-config prod

# This creates a production-ready wrangler.jsonc with:
# - Your account ID
# - R2 bucket bindings
# - Environment variables
# - Security settings
```

### 2. Generate R2 Connection Manifest

```bash
# Generate connection manifest for external tools
just r2:gen-manifest prod

# Creates: generated/r2-connection-manifest-prod.json
# Used by: AWS SDK, external services, monitoring tools
```

### 3. Validate Configuration

```bash
# Validate all configurations
just r2:validate prod

# Check for:
# - Valid account ID format
# - Bucket name compliance
# - Credential format validation
# - Security policy compliance
```

## 🌍 Multi-Environment Setup

### Environment Structure

```
secrets/
├── r2.yaml              # Production configuration
├── r2-staging.yaml      # Staging configuration
└── r2-development.yaml  # Development configuration
```

### Staging Environment

```bash
# Set up staging environment
cp secrets/r2.yaml secrets/r2-staging.yaml
just secrets:edit secrets/r2-staging.yaml

# Update for staging:
# - Different bucket names (add -staging suffix)
# - Different CORS origins
# - Less strict security for testing

# Generate staging configuration
just r2:gen-config stg
just r2:validate stg
```

### Development Environment

```bash
# Set up development environment
cp secrets/r2.yaml secrets/r2-development.yaml
just secrets:edit secrets/r2-development.yaml

# Update for development:
# - Development bucket names (add -dev suffix)
# - Relaxed CORS for local development
# - Debug logging enabled

# Generate development configuration
just r2:gen-config dev
just r2:validate dev
```

## 🔧 Wrangler Authentication

### 1. Authenticate Wrangler

```bash
# Login to Cloudflare
wrangler auth login

# Or use API token
export CLOUDFLARE_API_TOKEN="your-api-token"
```

### 2. Verify Authentication

```bash
# Check authentication status
wrangler whoami

# Test R2 access
wrangler r2 bucket list
```

## 🚀 Deployment Process

### 1. Pre-Deployment Validation

```bash
# Comprehensive pre-deployment check
just r2:deploy-prep prod

# This runs:
# - Configuration generation
# - Security validation
# - Secret encryption check
# - Syntax validation
```

### 2. Deploy to Production

```bash
# Deploy your Worker
wrangler deploy

# Deploy specific environment
wrangler deploy --env production

# Verify deployment
curl https://your-worker.your-subdomain.workers.dev/health
```

### 3. Post-Deployment Verification

```bash
# Test R2 operations in production
curl -X POST https://your-worker.your-subdomain.workers.dev/api/test-r2

# Check logs
wrangler tail

# Monitor metrics in Cloudflare Dashboard
```

## 🔒 Security Best Practices

### 1. Credential Management

```bash
# ✅ DO: Use encrypted secrets
just secrets:edit

# ✅ DO: Rotate credentials regularly
# Update secrets/r2.yaml with new credentials
just r2:gen-config prod
wrangler deploy

# ❌ DON'T: Store credentials in plain text
# ❌ DON'T: Commit secrets to git
# ❌ DON'T: Share credentials in chat/email
```

### 2. Access Control

```yaml
# In your R2 configuration
security:
  require_auth: true          # Always require authentication
  rate_limiting: true         # Enable rate limiting
  encryption_at_rest: true    # Use encryption at rest
  access_control: "strict"    # Strict access control

# Bucket-specific security
r2_buckets:
  - name: "sensitive-data"
    public_access: false      # Never public for sensitive data
    cors_origins:
      - "https://yourdomain.com"  # Specific origins only
```

### 3. Network Security

```typescript
// In your Worker code
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Validate origin
    const origin = request.headers.get('Origin');
    const allowedOrigins = ['https://yourdomain.com'];

    if (origin && !allowedOrigins.includes(origin)) {
      return new Response('Forbidden', { status: 403 });
    }

    // Validate authentication
    const authToken = request.headers.get('Authorization');
    if (!authToken || !isValidToken(authToken)) {
      return new Response('Unauthorized', { status: 401 });
    }

    // Continue with R2 operations...
  }
};
```

## 📊 Monitoring and Observability

### 1. Enable Worker Analytics

```jsonc
// In wrangler.jsonc
{
  "usage_model": "standard",
  "logpush": true,
  "analytics_engine_datasets": [
    {
      "binding": "ANALYTICS",
      "dataset": "r2_operations"
    }
  ]
}
```

### 2. Custom Metrics

```typescript
// Track R2 operations
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const startTime = Date.now();

    try {
      // R2 operation
      const result = await env.R2_BUCKET.get('file.txt');

      // Log success metrics
      env.ANALYTICS.writeDataPoint({
        operation: 'get',
        status: 'success',
        duration: Date.now() - startTime,
        bucket: 'production-bucket'
      });

      return new Response(result?.body);
    } catch (error) {
      // Log error metrics
      env.ANALYTICS.writeDataPoint({
        operation: 'get',
        status: 'error',
        error: error.message,
        duration: Date.now() - startTime
      });

      throw error;
    }
  }
};
```

### 3. Health Checks

```typescript
// Add health check endpoint
app.get('/health', async (c) => {
  try {
    // Test R2 connectivity
    await c.env.R2_BUCKET.head('health-check-object');

    return c.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      r2_connectivity: 'ok'
    });
  } catch (error) {
    return c.json({
      status: 'unhealthy',
      error: error.message,
      r2_connectivity: 'failed'
    }, 503);
  }
});
```

## 🔄 Backup and Disaster Recovery

### 1. Backup Strategy

```bash
# Create backup buckets
wrangler r2 bucket create my-production-backup
wrangler r2 bucket create my-production-archive

# Implement backup in your Worker
async function backupToSecondaryBucket(key: string, object: R2Object) {
  await env.R2_BACKUP_BUCKET.put(key, object.body, {
    customMetadata: {
      ...object.customMetadata,
      backedUpAt: new Date().toISOString(),
      originalBucket: 'production'
    }
  });
}
```

### 2. Cross-Region Considerations

```yaml
# Consider multiple regions for critical data
r2_buckets:
  - name: "production-primary"
    purpose: "primary-storage"
    region: "auto"  # Let Cloudflare choose optimal region

  - name: "production-backup"
    purpose: "backup-storage"
    region: "auto"
```

## 🚨 Troubleshooting Production Issues

### Common Issues and Solutions

1. **Authentication Errors**
   ```bash
   # Check API token permissions
   curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        "https://api.cloudflare.com/client/v4/user/tokens/verify"
   ```

2. **R2 Access Denied**
   ```bash
   # Verify R2 credentials
   just r2:validate prod

   # Check bucket permissions in dashboard
   ```

3. **CORS Issues**
   ```bash
   # Update CORS configuration
   just secrets:edit secrets/r2.yaml
   just r2:gen-config prod
   wrangler deploy
   ```

For more troubleshooting guidance, see [Troubleshooting Guide](troubleshooting.md).

## ⚡ Performance Optimization

### 1. Optimize R2 Operations

```typescript
// Use streams for large files
const uploadStream = new ReadableStream({
  start(controller) {
    // Stream data in chunks
    controller.enqueue(chunk);
  }
});

await env.R2_BUCKET.put('large-file.bin', uploadStream);
```

### 2. Implement Caching

```typescript
// Cache frequently accessed objects
const CACHE_TTL = 3600; // 1 hour

app.get('/files/:key', async (c) => {
  const cacheKey = `r2:${c.req.param('key')}`;

  // Try cache first
  const cached = await c.env.KV_CACHE.get(cacheKey, 'stream');
  if (cached) {
    return new Response(cached, {
      headers: { 'X-Cache': 'HIT' }
    });
  }

  // Fetch from R2
  const object = await c.env.R2_BUCKET.get(c.req.param('key'));
  if (!object) {
    return c.notFound();
  }

  // Cache for future requests
  await c.env.KV_CACHE.put(cacheKey, object.body, {
    expirationTtl: CACHE_TTL
  });

  return new Response(object.body, {
    headers: { 'X-Cache': 'MISS' }
  });
});
```

## 📚 Next Steps

After setting up production R2:

1. **[AWS SDK Integration](aws-sdk-integration.md)** - Use R2 with AWS SDK v3
2. **[Security Guide](security-guide.md)** - Advanced security configurations
3. **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
4. **[Environment Management](environment-management.md)** - Advanced multi-env setup