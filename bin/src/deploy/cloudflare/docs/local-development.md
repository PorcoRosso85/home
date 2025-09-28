# 🧪 Local Development Guide

Complete guide for R2 Resource Plane development using Miniflare - no Cloudflare account required!

## 🎯 What is Miniflare?

Miniflare is a simulator for Cloudflare Workers that runs locally on your machine. It provides:

- **✅ Full R2 Configuration Simulation**: All resource management operations work exactly like real R2
- **✅ Zero Authentication**: No API keys, tokens, or Cloudflare account needed
- **✅ Instant Feedback**: No network latency, immediate responses
- **✅ Side-Effect Free**: No real buckets are created or modified
- **✅ Perfect for Testing**: Ideal for configuration validation, integration tests, and development

## 🚀 Quick Setup

### 1. Initialize Development Environment

```bash
# Enter the Nix development shell
nix develop

# Set up basic configuration
nix run .#r2-dev-workflow -- setup

# Verify everything is working
nix run .#status
```

### 2. Test R2 Configuration Locally

```bash
# Run the local R2 configuration test suite
nix run .#r2-dev-workflow -- test dev

# This will test:
# - Bucket configuration validation
# - Resource settings verification
# - Configuration error handling
# - Environment setup validation
```

### 3. Start Development Server

```bash
# Start Wrangler in local mode with Miniflare
wrangler dev --local

# Your Worker will be available at:
# http://localhost:8787
```

## 🧪 Testing R2 Configuration Management

### Resource Configuration Validation

Here's how to test R2 resource management locally:

```typescript
// In your Worker code - Resource Plane operations
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { R2_BUCKET } = env;

    // Verify bucket binding configuration
    if (!R2_BUCKET) {
      return new Response('R2 bucket binding not configured', { status: 500 });
    }

    // Test bucket accessibility and configuration
    try {
      // Simple bucket access test (not data operation)
      const bucketInfo = await R2_BUCKET.head('config-test-marker');
      return new Response('Bucket configuration valid', { status: 200 });
    } catch (error) {
      return new Response(`Configuration error: ${error.message}`, { status: 500 });
    }
  }
};
```

### Configuration Validation Patterns

```typescript
// Environment and resource validation
interface ResourceValidation {
  bucketBinding: boolean;
  environmentConfig: boolean;
  secretsAccess: boolean;
}

async function validateResourceConfiguration(env: Env): Promise<ResourceValidation> {
  return {
    bucketBinding: !!env.R2_BUCKET,
    environmentConfig: env.ENVIRONMENT === 'development',
    secretsAccess: !!env.API_SECRET
  };
}

// Configuration deployment verification
async function verifyDeploymentConfig(env: Env): Promise<Response> {
  const validation = await validateResourceConfiguration(env);

  if (!validation.bucketBinding) {
    return new Response('Missing R2 bucket binding', { status: 500 });
  }

  return new Response('Resource configuration verified', { status: 200 });
}
```

> **📚 Data Plane Operations**: For actual data operations (PUT/GET/DELETE/LIST), see the educational examples in [`examples/r2-data-operations/`](../examples/r2-data-operations/) directory. This document focuses on Resource Plane management and configuration validation.

## 🧩 Configuration Integration Examples

### With Hono Framework - Resource Management

```typescript
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Env }>();

// Resource configuration endpoint
app.get('/api/config/status', async (c) => {
  try {
    const validation = await validateResourceConfiguration(c.env);

    return c.json({
      status: 'healthy',
      resources: {
        r2Bucket: validation.bucketBinding ? 'configured' : 'missing',
        environment: c.env.ENVIRONMENT || 'not-set',
        secretsAvailable: validation.secretsAccess
      }
    });
  } catch (error) {
    return c.json({
      status: 'error',
      message: error.message
    }, 500);
  }
});

// Configuration validation endpoint
app.post('/api/config/validate', async (c) => {
  const config = await c.req.json();

  // Validate configuration settings
  const errors = [];
  if (!config.bucketName) errors.push('Missing bucket name');
  if (!config.environment) errors.push('Missing environment');

  if (errors.length > 0) {
    return c.json({ valid: false, errors }, 400);
  }

  return c.json({ valid: true, message: 'Configuration valid' });
});

export default app;
```

### Resource Verification Integration

```typescript
// Configuration verification module
interface DeploymentConfig {
  bucketBinding: string;
  environment: 'development' | 'staging' | 'production';
  secretsConfigured: boolean;
}

async function verifyDeploymentReadiness(env: Env): Promise<DeploymentConfig> {
  return {
    bucketBinding: env.R2_BUCKET ? 'ready' : 'not-configured',
    environment: env.ENVIRONMENT as any || 'development',
    secretsConfigured: !!(env.API_SECRET && env.DEPLOYMENT_KEY)
  };
}

// In your application startup
app.get('/api/health', async (c) => {
  const config = await verifyDeploymentReadiness(c.env);

  const isReady = config.bucketBinding === 'ready' && config.secretsConfigured;

  return c.json({
    status: isReady ? 'ready' : 'not-ready',
    config
  }, isReady ? 200 : 503);
});
```

> **📚 Data Operations Examples**: For actual file upload/download implementations, see [`examples/r2-data-operations/`](../examples/r2-data-operations/) which contains educational examples for Data Plane operations.

## 🔧 Development Configuration

### Wrangler Configuration for Local Development

Your `wrangler.jsonc` should include:

```jsonc
{
  "name": "my-r2-app",
  "main": "src/worker.ts",
  "compatibility_date": "2024-09-01",
  "r2_buckets": [
    {
      "binding": "R2_BUCKET",
      "bucket_name": "my-local-bucket"
    }
  ],
  // Local development settings
  "dev": {
    "local": true,
    "port": 8787
  }
}
```

### Environment Variables for Local Testing

```bash
# Create .dev.vars for local environment variables
echo "DEBUG=true" > .dev.vars
echo "ENVIRONMENT=development" >> .dev.vars

# These will be available in your Worker as env.DEBUG, env.ENVIRONMENT
```

## 🧪 Testing Strategies

### Resource Configuration Testing with Miniflare

```typescript
// test/r2-config.test.ts
import { unstable_dev } from 'wrangler';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

describe('R2 Configuration Management', () => {
  let worker: any;

  beforeAll(async () => {
    worker = await unstable_dev('src/worker.ts', {
      experimental: { disableExperimentalWarning: true }
    });
  });

  afterAll(async () => {
    await worker.stop();
  });

  it('should validate resource configuration', async () => {
    const response = await worker.fetch('/api/config/status');
    expect(response.status).toBe(200);

    const config = await response.json();
    expect(config.status).toBe('healthy');
    expect(config.resources.r2Bucket).toBe('configured');
  });

  it('should handle configuration validation', async () => {
    const response = await worker.fetch('/api/config/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bucketName: 'test-bucket', environment: 'dev' })
    });
    expect(response.status).toBe(200);

    const result = await response.json();
    expect(result.valid).toBe(true);
  });

  it('should detect missing configuration', async () => {
    const response = await worker.fetch('/api/config/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}) // Empty configuration
    });
    expect(response.status).toBe(400);

    const result = await response.json();
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Missing bucket name');
  });
});
```

### Configuration Integration Testing

```bash
# Run comprehensive resource configuration tests
nix run .#r2-dev-workflow -- test dev

# This runs tests for:
# - Resource binding validation
# - Configuration settings verification
# - Environment setup validation
# - Deployment readiness checks
```

> **📚 Data Operation Testing**: For testing actual data operations, see the test examples in [`examples/r2-data-operations/`](../examples/r2-data-operations/) directory.

## 🎭 Debugging and Configuration Tips

### 1. Enable Configuration Debug Logging

```typescript
// In your Worker - Resource configuration debugging
console.log('Resource configuration:', {
  operation: 'CONFIG_CHECK',
  bucketBinding: !!env.R2_BUCKET,
  environment: env.ENVIRONMENT,
  secretsCount: Object.keys(env).filter(k => k.includes('SECRET')).length
});

// Logs will appear in wrangler dev console
```

### 2. Inspect Resource State

```bash
# View Miniflare configuration state
ls -la .wrangler/state/v3/

# Check environment bindings
cat .wrangler/state/v3/bindings.json

# Note: Configuration state persists between restarts if enabled
```

### 3. Mock Configuration Scenarios

```typescript
// Simulate different configuration states for testing
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Simulate missing configuration for testing error handling
    if (url.pathname.includes('/simulate-config-error')) {
      // Test configuration error handling
      return new Response('Missing required configuration', { status: 500 });
    }

    // Test deployment readiness
    if (url.pathname.includes('/check-deployment')) {
      const config = await verifyDeploymentReadiness(env);
      return Response.json(config);
    }

    // Normal operation
    return handleRequest(request, env);
  }
};
```

## ⚠️ Local Development Limitations

### What Miniflare Simulates Well for Resource Management
- ✅ R2 bucket binding configuration
- ✅ Environment variable access
- ✅ Resource availability validation
- ✅ Configuration error simulation
- ✅ Deployment readiness checks

### What Miniflare Doesn't Simulate for Resource Management
- ❌ Real Cloudflare account integration
- ❌ Actual bucket creation/deletion operations
- ❌ Real billing and quota enforcement
- ❌ Cross-account resource sharing
- ❌ Real CDN configuration propagation
- ❌ Actual secrets manager integration

### Migration Notes for Resource Management
- Configuration validation written for Miniflare works identically with real Cloudflare
- Test resource provisioning thoroughly in staging environment before production
- Monitor actual resource usage and costs in production
- Validate IAM and security configurations in real environment

> **📚 Data Operation Limitations**: For information about Data Plane operation limitations in Miniflare, see [`examples/r2-data-operations/README.md`](../examples/r2-data-operations/README.md).

## 🚀 Ready for Production?

When you're ready to move from local development to production:

1. **Read the [Production Setup Guide](production-setup.md)**
2. **Set up encrypted secrets**: `just secrets-init`
3. **Configure your R2 credentials**: `just secrets-edit`
4. **Test in staging environment first**
5. **Deploy with**: `just r2:deploy-prep prod && wrangler deploy`

## 📚 Additional Resources

- **[Miniflare Documentation](https://miniflare.dev/)** - Local Cloudflare Workers simulation
- **[Cloudflare R2 Configuration](https://developers.cloudflare.com/r2/)** - Resource management documentation
- **[Wrangler Local Development](https://developers.cloudflare.com/workers/wrangler/commands/#dev)** - Local development setup
- **[Resource Management Examples](../examples/)** - Configuration and setup examples
- **[Data Operation Examples](../examples/r2-data-operations/)** - Educational Data Plane operation examples
