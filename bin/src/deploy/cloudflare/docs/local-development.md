# 🧪 Local Development Guide

Complete guide for R2 development using Miniflare - no Cloudflare account required!

## 🎯 What is Miniflare?

Miniflare is a simulator for Cloudflare Workers that runs locally on your machine. It provides:

- **✅ Full R2 API Simulation**: All storage operations work exactly like real R2
- **✅ Zero Authentication**: No API keys, tokens, or Cloudflare account needed
- **✅ Instant Feedback**: No network latency, immediate responses
- **✅ Side-Effect Free**: No real buckets are created or modified
- **✅ Perfect for Testing**: Ideal for unit tests, integration tests, and development

## 🚀 Quick Setup

### 1. Initialize Development Environment

```bash
# Enter the Nix development shell
nix develop

# Set up basic configuration
just setup

# Verify everything is working
just status
```

### 2. Test R2 Operations Locally

```bash
# Run the local R2 test suite
just r2:test dev

# This will test:
# - Bucket operations (create, list, delete)
# - Object operations (put, get, head, delete)
# - Error handling
# - Metadata operations
```

### 3. Start Development Server

```bash
# Start Wrangler in local mode with Miniflare
wrangler dev --local

# Your Worker will be available at:
# http://localhost:8787
```

## 🧪 Testing R2 Operations

### Basic CRUD Operations

Here's how to test all R2 operations locally:

```typescript
// In your Worker code
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { R2_BUCKET } = env;

    // PUT: Upload an object
    await R2_BUCKET.put('test-file.txt', 'Hello, R2!', {
      metadata: {
        uploadedAt: new Date().toISOString(),
        contentType: 'text/plain'
      }
    });

    // GET: Retrieve an object
    const object = await R2_BUCKET.get('test-file.txt');
    const content = await object?.text();

    // HEAD: Get object metadata
    const metadata = await R2_BUCKET.head('test-file.txt');

    // LIST: List objects in bucket
    const list = await R2_BUCKET.list();

    // DELETE: Remove an object
    await R2_BUCKET.delete('test-file.txt');

    return new Response(`Content: ${content}`);
  }
};
```

### Advanced Operations

```typescript
// Multipart uploads (simulated)
const upload = await R2_BUCKET.createMultipartUpload('large-file.bin');

// Conditional operations
const result = await R2_BUCKET.put('file.txt', data, {
  onlyIf: { etagMatches: 'expected-etag' }
});

// Custom metadata and HTTP metadata
await R2_BUCKET.put('document.pdf', pdfData, {
  customMetadata: {
    documentType: 'invoice',
    processedBy: 'system-v2'
  },
  httpMetadata: {
    contentType: 'application/pdf',
    cacheControl: 'max-age=3600'
  }
});
```

## 🧩 Integration Examples

### With Hono Framework

```typescript
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Env }>();

app.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return c.json({ error: 'No file provided' }, 400);
  }

  // Upload to R2 (Miniflare simulation)
  await c.env.R2_BUCKET.put(file.name, file.stream(), {
    customMetadata: {
      originalName: file.name,
      uploadedAt: new Date().toISOString()
    }
  });

  return c.json({ message: 'File uploaded successfully' });
});

app.get('/files/:key', async (c) => {
  const key = c.req.param('key');
  const object = await c.env.R2_BUCKET.get(key);

  if (!object) {
    return c.json({ error: 'File not found' }, 404);
  }

  return new Response(object.body, {
    headers: {
      'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream'
    }
  });
});

export default app;
```

### With React/Frontend Integration

```typescript
// In your Worker
app.get('/api/signed-url/:key', async (c) => {
  const key = c.req.param('key');

  // Note: In Miniflare, presigned URLs are simulated
  // Real R2 would generate actual presigned URLs
  const signedUrl = `http://localhost:8787/api/files/${key}`;

  return c.json({ signedUrl, expiresIn: 3600 });
});

// In your React component
async function uploadFile(file: File) {
  // Upload directly through Worker API
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
  });

  if (response.ok) {
    console.log('File uploaded successfully!');
  }
}
```

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

### Unit Testing with Miniflare

```typescript
// test/r2-operations.test.ts
import { unstable_dev } from 'wrangler';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

describe('R2 Operations', () => {
  let worker: any;

  beforeAll(async () => {
    worker = await unstable_dev('src/worker.ts', {
      experimental: { disableExperimentalWarning: true }
    });
  });

  afterAll(async () => {
    await worker.stop();
  });

  it('should upload and retrieve files', async () => {
    // Upload a file
    const uploadResponse = await worker.fetch('/api/upload', {
      method: 'POST',
      body: new FormData().append('file', new File(['test'], 'test.txt'))
    });
    expect(uploadResponse.status).toBe(200);

    // Retrieve the file
    const downloadResponse = await worker.fetch('/api/files/test.txt');
    expect(downloadResponse.status).toBe(200);
    expect(await downloadResponse.text()).toBe('test');
  });

  it('should handle file not found', async () => {
    const response = await worker.fetch('/api/files/nonexistent.txt');
    expect(response.status).toBe(404);
  });
});
```

### Integration Testing

```bash
# Run comprehensive integration tests
just r2:test dev

# This runs tests for:
# - Basic CRUD operations
# - Error conditions
# - Metadata handling
# - Concurrent operations
```

## 🎭 Debugging and Development Tips

### 1. Enable Debug Logging

```typescript
// In your Worker
console.log('R2 operation:', {
  operation: 'PUT',
  key: 'file.txt',
  size: data.length
});

// Logs will appear in wrangler dev console
```

### 2. Inspect Miniflare State

```bash
# View Miniflare persistence directory (if enabled)
ls -la .wrangler/state/v3/r2

# Note: By default, Miniflare doesn't persist data between restarts
```

### 3. Mock Different Scenarios

```typescript
// Simulate different R2 responses for testing
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Simulate errors for testing error handling
    if (url.pathname.includes('/simulate-error')) {
      // This will test your error handling code
      throw new Error('Simulated R2 error');
    }

    // Normal operation
    return handleRequest(request, env);
  }
};
```

## ⚠️ Local Development Limitations

### What Miniflare Simulates Well
- ✅ All R2 API methods (put, get, head, delete, list)
- ✅ Metadata operations
- ✅ Error conditions and status codes
- ✅ Basic multipart upload simulation
- ✅ Object streams and binary data

### What Miniflare Doesn't Simulate
- ❌ Real presigned URLs (generates mock URLs)
- ❌ Cloudflare CDN integration
- ❌ R2 event notifications
- ❌ Cross-region replication
- ❌ Real billing and usage metrics
- ❌ Network latency and real-world performance characteristics

### Migration Notes
- Code written for Miniflare works identically with real R2
- Test thoroughly in staging environment before production
- Monitor actual usage patterns in production

## 🚀 Ready for Production?

When you're ready to move from local development to production:

1. **Read the [Production Setup Guide](production-setup.md)**
2. **Set up encrypted secrets**: `just secrets-init`
3. **Configure your R2 credentials**: `just secrets-edit`
4. **Test in staging environment first**
5. **Deploy with**: `just r2:deploy-prep prod && wrangler deploy`

## 📚 Additional Resources

- **[Miniflare Documentation](https://miniflare.dev/)**
- **[Cloudflare R2 API Reference](https://developers.cloudflare.com/r2/api/)**
- **[Wrangler Local Development](https://developers.cloudflare.com/workers/wrangler/commands/#dev)**
- **[Integration Examples](../examples/)** - More code examples