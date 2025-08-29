# Workers-Only Architecture

## ⚠️ Important: No Node.js Dependencies

This project is designed to run **exclusively** in Cloudflare Workers environment.

### ❌ Prohibited (Will NOT work)
```javascript
// These will fail in Workers:
import * as fs from 'fs';        // ❌ No filesystem
import * as path from 'path';    // ❌ No path module
import { exec } from 'child_process';  // ❌ No process
```

### ✅ Allowed (Workers-compatible)
```javascript
// Use these instead:
console.log()           // → Cloudflare Logs
env.KV.put()           // → KV Storage
env.R2.put()           // → R2 Object Storage
env.DB.prepare()       // → D1 Database
```

## Architecture Overview

```
Form Submission
      ↓
console.log (structured JSON)
      ↓
Cloudflare Logs (real-time)
      ↓
Optional: KV Buffer
      ↓
Scheduled Worker (cron)
      ↓
R2 Storage (JSONL files)
      ↓
DuckDB Analysis
```

## Setup Instructions

### 1. Create KV Namespace
```bash
npx wrangler kv:namespace create "SUBMISSIONS_KV"
# Copy the ID to wrangler.toml
```

### 2. Create R2 Bucket
```bash
npx wrangler r2 bucket create waku-data
```

### 3. Deploy
```bash
npx wrangler deploy
```

### 4. Monitor Logs
```bash
# Real-time log tailing
npx wrangler tail

# View in dashboard
# https://dash.cloudflare.com/workers-and-pages
```

## Testing

### Local Testing (with limitations)
```bash
npx wrangler dev
# Note: KV and R2 are simulated locally
```

### Edge Testing (full features)
```bash
npx wrangler dev --local=false
# Uses actual Cloudflare infrastructure
```

## Key Differences from Node.js

| Feature | Node.js | Workers |
|---------|---------|---------|
| File System | ✅ fs module | ❌ Use R2/KV |
| Environment Variables | process.env | env object |
| Async Context | async/await | ✅ Same |
| HTTP Requests | fetch/axios | ✅ fetch only |
| Timers | setTimeout | ❌ Use Scheduled Workers |
| Streams | Node streams | ✅ Web Streams API |

## Common Patterns

### Logging
```typescript
// Structured logging for better parsing
console.log(JSON.stringify({
  timestamp: Date.now(),
  level: 'info',
  message: 'User action',
  data: { userId: '123' }
}));
```

### Buffering with KV
```typescript
// Temporary storage before batch processing
await env.KV.put(
  `buffer:${Date.now()}`,
  JSON.stringify(data),
  { expirationTtl: 3600 } // 1 hour TTL
);
```

### Scheduled Processing
```typescript
// In scheduled handler
export default {
  async scheduled(event, env, ctx) {
    // Process buffered data
    const list = await env.KV.list({ prefix: 'buffer:' });
    // ... aggregate and store to R2
  }
}
```

## Debugging Tips

1. **Use wrangler tail** for real-time log monitoring
2. **Check KV contents**: `npx wrangler kv:key list --namespace-id=...`
3. **List R2 objects**: `npx wrangler r2 object list waku-data`
4. **Test scheduled workers**: `npx wrangler dev --test-scheduled`

## Resources

- [Workers Runtime APIs](https://developers.cloudflare.com/workers/runtime-apis/)
- [KV Documentation](https://developers.cloudflare.com/workers/runtime-apis/kv/)
- [R2 Documentation](https://developers.cloudflare.com/r2/)
- [Scheduled Workers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)