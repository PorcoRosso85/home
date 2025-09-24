# 🔧 Troubleshooting Guide

Complete troubleshooting guide for common issues with the R2 Connection Management System.

## 🚨 Quick Diagnosis

### Run System Health Check

```bash
# Check overall system status
just status

# Validate specific environment
just r2:validate prod

# Check for plaintext secrets
just secrets:check

# Verify all configurations
just r2:validate-all
```

### Common Quick Fixes

```bash
# Regenerate configurations
just clean && just setup

# Refresh secrets encryption
just secrets:edit

# Reset development environment
nix develop --refresh
```

## 🔐 Authentication & Credentials Issues

### ❌ "Unauthorized" or "Access Denied" Errors

**Symptoms:**
- 401 Unauthorized responses
- 403 Forbidden errors
- "Invalid credentials" messages

**Diagnosis:**
```bash
# Check if credentials are properly encrypted
just secrets:check

# Verify R2 credentials format
just secrets:edit secrets/r2.yaml

# Test authentication
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
     "https://api.cloudflare.com/client/v4/user/tokens/verify"
```

**Solutions:**

1. **Regenerate R2 API Credentials:**
   ```bash
   # In Cloudflare Dashboard:
   # R2 Object Storage → Manage R2 API tokens → Create API token

   # Update secrets with new credentials
   just secrets:edit secrets/r2.yaml
   just r2:gen-config prod
   ```

2. **Check Cloudflare API Token:**
   ```bash
   # Verify token has correct permissions:
   # - Cloudflare Workers:Edit
   # - Account:R2:Edit (or specific buckets)

   wrangler whoami
   ```

3. **Validate Account ID:**
   ```bash
   # Ensure account ID is correct 32-character hex string
   # Check in: Cloudflare Dashboard → Right sidebar

   just secrets:edit secrets/r2.yaml
   # Update cf_account_id field
   ```

### ❌ "Invalid API Token" Errors

**Solutions:**
```bash
# Re-authenticate with Wrangler
wrangler auth login

# Or set token directly
export CLOUDFLARE_API_TOKEN="your-new-token"

# Verify authentication
wrangler whoami
```

## 🧪 Local Development Issues

### ❌ Miniflare Not Starting

**Symptoms:**
- `wrangler dev --local` fails to start
- "Port already in use" errors
- Miniflare crashes on startup

**Solutions:**

1. **Kill existing processes:**
   ```bash
   # Find and kill processes using port 8787
   lsof -i :8787
   kill -9 <PID>

   # Or use different port
   wrangler dev --local --port 8788
   ```

2. **Clear Wrangler cache:**
   ```bash
   rm -rf .wrangler/
   wrangler dev --local
   ```

3. **Check Node.js version:**
   ```bash
   # Ensure Node.js 18+ is installed
   node --version

   # Use Nix environment
   nix develop
   node --version
   ```

### ❌ "R2 Bucket Not Found" in Local Development

**Symptoms:**
- R2 operations fail locally
- "NoSuchBucket" errors in Miniflare

**Solutions:**

1. **Check wrangler.jsonc configuration:**
   ```bash
   # Verify R2 bindings are present
   cat wrangler.jsonc | jq '.r2_buckets'

   # Regenerate if missing
   just r2:gen-config dev
   ```

2. **Restart Wrangler dev:**
   ```bash
   # Stop current dev server (Ctrl+C)
   # Clear cache and restart
   rm -rf .wrangler/
   wrangler dev --local
   ```

### ❌ Local R2 Test Failures

**Diagnosis:**
```bash
# Run test with verbose output
just r2:test dev

# Check test script directly
nix run .#test-r2-local
```

**Solutions:**

1. **Missing test dependencies:**
   ```bash
   # Ensure in Nix environment
   nix develop

   # Check if test script exists
   ls -la scripts/test-r2-local.sh
   ```

2. **Port conflicts:**
   ```bash
   # Use different port for testing
   WRANGLER_PORT=8788 just r2:test dev
   ```

## 🚀 Production Deployment Issues

### ❌ Deployment Fails with "Account ID Mismatch"

**Symptoms:**
- `wrangler deploy` fails
- "Account ID does not match" errors

**Solutions:**

1. **Verify account ID in configuration:**
   ```bash
   # Check account ID in wrangler.jsonc
   cat wrangler.jsonc | jq '.account_id'

   # Compare with Cloudflare Dashboard
   # Update if necessary
   just secrets:edit secrets/r2.yaml
   just r2:gen-config prod
   ```

2. **Check Wrangler authentication:**
   ```bash
   wrangler whoami
   # Should show correct account

   # Re-authenticate if needed
   wrangler auth login
   ```

### ❌ "Bucket Does Not Exist" in Production

**Symptoms:**
- R2 operations fail in deployed Worker
- NoSuchBucket errors in production

**Solutions:**

1. **Create missing buckets:**
   ```bash
   # List existing buckets
   wrangler r2 bucket list

   # Create missing buckets
   wrangler r2 bucket create my-production-bucket
   wrangler r2 bucket create my-static-assets
   ```

2. **Check bucket binding configuration:**
   ```bash
   # Verify bucket bindings in wrangler.jsonc
   cat wrangler.jsonc | jq '.r2_buckets'

   # Ensure bucket names match actual R2 buckets
   ```

### ❌ CORS Issues in Production

**Symptoms:**
- Browser CORS errors
- Cross-origin requests blocked
- "Access-Control-Allow-Origin" missing

**Solutions:**

1. **Configure CORS in Worker:**
   ```typescript
   // Add CORS headers to responses
   const corsHeaders = {
     'Access-Control-Allow-Origin': 'https://yourdomain.com',
     'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
     'Access-Control-Allow-Headers': 'Content-Type, Authorization',
   };

   return new Response(data, { headers: corsHeaders });
   ```

2. **Update R2 bucket CORS configuration:**
   ```bash
   # Update CORS origins in secrets
   just secrets:edit secrets/r2.yaml

   # Add/update cors_origins for your buckets:
   # r2_buckets:
   #   - name: "my-bucket"
   #     cors_origins:
   #       - "https://yourdomain.com"
   #       - "https://www.yourdomain.com"

   just r2:gen-config prod
   wrangler deploy
   ```

## 🔧 Configuration Issues

### ❌ "Invalid Configuration" Errors

**Symptoms:**
- Schema validation failures
- "Configuration does not match schema" errors
- JSON parsing errors

**Diagnosis:**
```bash
# Validate configuration against schema
just r2:validate prod

# Check configuration syntax
cat generated/r2-connection-manifest-prod.json | jq '.'
```

**Solutions:**

1. **Fix configuration format:**
   ```bash
   # Edit raw configuration
   just secrets:edit secrets/r2.yaml

   # Common fixes:
   # - Ensure account_id is 32-character hex string
   # - Check bucket names follow S3 naming rules
   # - Verify CORS origins are valid URLs
   ```

2. **Regenerate from template:**
   ```bash
   # Start fresh from example
   cp r2.yaml.example secrets/r2.yaml
   just secrets:edit secrets/r2.yaml
   just r2:gen-config prod
   ```

### ❌ Missing Generated Files

**Symptoms:**
- `generated/` directory empty
- Connection manifests not found
- wrangler.jsonc missing

**Solutions:**

1. **Regenerate all configurations:**
   ```bash
   # Clean and regenerate everything
   just clean
   just setup
   just r2:gen-all prod
   ```

2. **Check permissions:**
   ```bash
   # Ensure write permissions
   ls -la generated/
   chmod 755 generated/
   ```

## 🔒 Security Issues

### ❌ "Plaintext Secrets Detected" Errors

**Symptoms:**
- `nix flake check` fails
- CI/CD builds fail
- Security warnings

**Diagnosis:**
```bash
# Check for plaintext secrets
just secrets:check

# See detailed output
nix build .#checks.x86_64-linux.no-plaintext-secrets
```

**Solutions:**

1. **Encrypt exposed secrets:**
   ```bash
   # Move secrets to encrypted storage
   just secrets:edit secrets/r2.yaml

   # Remove from plain files
   git rm file-with-secrets.txt

   # Add to .gitignore
   echo "*.secret" >> .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **Clean git history if secrets were committed:**
   ```bash
   # DANGEROUS: Rewrites git history
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch secrets-file.txt' \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (coordinate with team)
   git push --force --all
   ```

### ❌ Age Encryption Issues

**Symptoms:**
- Cannot edit secrets
- "Failed to decrypt" errors
- Age key not found

**Solutions:**

1. **Initialize Age encryption:**
   ```bash
   # Generate new Age key
   just secrets:init

   # Verify key exists
   ls -la ~/.config/sops/age/keys.txt
   ```

2. **Fix SOPS configuration:**
   ```bash
   # Check .sops.yaml exists and is valid
   cat .sops.yaml

   # Should contain your Age public key
   ```

## 🌐 Network and Connectivity Issues

### ❌ "Network Timeout" Errors

**Symptoms:**
- Slow or failing R2 operations
- Timeout errors in production
- Intermittent connectivity issues

**Solutions:**

1. **Optimize connection settings:**
   ```typescript
   // In AWS SDK configuration
   const r2Client = new S3Client({
     region: 'auto',
     endpoint: R2_ENDPOINT,
     credentials: R2_CREDENTIALS,
     requestHandler: {
       connectionTimeout: 10000, // 10 seconds
       socketTimeout: 30000,     // 30 seconds
     },
     maxAttempts: 3
   });
   ```

2. **Check network connectivity:**
   ```bash
   # Test R2 endpoint connectivity
   curl -I https://your-account-id.r2.cloudflarestorage.com

   # Check DNS resolution
   nslookup your-account-id.r2.cloudflarestorage.com
   ```

### ❌ "DNS Resolution Failed" Errors

**Solutions:**

1. **Use alternative DNS:**
   ```bash
   # Add to /etc/resolv.conf (or use system settings)
   nameserver 1.1.1.1
   nameserver 8.8.8.8
   ```

2. **Check corporate firewall/proxy:**
   ```bash
   # Test with proxy settings
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

## 🧪 Testing Issues

### ❌ Integration Tests Failing

**Symptoms:**
- `just r2:validate-all` fails
- Test timeouts
- Inconsistent test results

**Solutions:**

1. **Run tests individually:**
   ```bash
   # Test each environment separately
   just r2:validate dev
   just r2:validate stg
   just r2:validate prod
   ```

2. **Check test environment:**
   ```bash
   # Ensure test buckets exist
   wrangler r2 bucket list | grep test

   # Create if missing
   wrangler r2 bucket create integration-test-bucket
   ```

3. **Clear test data:**
   ```bash
   # Clean up test objects
   wrangler r2 object delete integration-test-bucket --prefix "test-"
   ```

## 📊 Performance Issues

### ❌ Slow R2 Operations

**Symptoms:**
- High latency in R2 operations
- Timeouts on large uploads
- Poor performance compared to local testing

**Solutions:**

1. **Optimize upload strategy:**
   ```typescript
   // Use multipart upload for large files
   if (fileSize > 5 * 1024 * 1024) { // 5MB
     return await multipartUpload(bucket, key, data);
   } else {
     return await singleUpload(bucket, key, data);
   }
   ```

2. **Implement retry logic:**
   ```typescript
   async function retryOperation<T>(operation: () => Promise<T>, maxRetries = 3): Promise<T> {
     for (let i = 0; i < maxRetries; i++) {
       try {
         return await operation();
       } catch (error) {
         if (i === maxRetries - 1) throw error;
         await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
       }
     }
     throw new Error('Max retries exceeded');
   }
   ```

3. **Use connection pooling:**
   ```typescript
   // Configure HTTP agent for connection pooling
   import { NodeHttpHandler } from '@aws-sdk/node-http-handler';

   const r2Client = new S3Client({
     region: 'auto',
     endpoint: R2_ENDPOINT,
     credentials: R2_CREDENTIALS,
     requestHandler: new NodeHttpHandler({
       connectionTimeout: 5000,
       socketTimeout: 10000,
       httpAgent: new Agent({
         keepAlive: true,
         maxSockets: 50
       })
     })
   });
   ```

## 🔍 Debugging Techniques

### Enable Verbose Logging

```bash
# Enable debug logging for Wrangler
export WRANGLER_LOG=debug
wrangler dev --local

# Enable debug for testing
export DEBUG=true
just r2:test dev
```

### Check Wrangler Logs

```bash
# View live logs from deployed Worker
wrangler tail

# View logs with filters
wrangler tail --format pretty --filter error
```

### Inspect Network Traffic

```bash
# Use curl to test R2 endpoints directly
curl -v -X GET "https://account-id.r2.cloudflarestorage.com/bucket-name" \
  -H "Authorization: Bearer $R2_TOKEN"
```

### Debug Configuration Loading

```typescript
// Add debug logging to your Worker
console.log('Environment:', {
  NODE_ENV: process.env.NODE_ENV,
  R2_BUCKET: env.R2_BUCKET ? 'configured' : 'missing',
  ACCOUNT_ID: env.ACCOUNT_ID?.substring(0, 8) + '...'
});
```

## 📱 Platform-Specific Issues

### macOS Issues

**Common problems:**
- Keychain authentication conflicts
- Node.js version mismatches

**Solutions:**
```bash
# Clear Wrangler auth
rm -rf ~/.wrangler/
wrangler auth login

# Use Nix for consistent Node.js
nix develop
```

### Linux Issues

**Common problems:**
- Permission errors
- Missing system dependencies

**Solutions:**
```bash
# Fix permissions
sudo chown -R $USER:$USER ~/.config/sops/
chmod 600 ~/.config/sops/age/keys.txt

# Install system dependencies via Nix
nix develop
```

### Windows/WSL Issues

**Common problems:**
- Path separator issues
- CRLF line ending problems

**Solutions:**
```bash
# Set git to handle line endings
git config --global core.autocrlf true

# Use WSL2 for better compatibility
wsl --set-version Ubuntu 2
```

## ❓ FAQ

### Q: Can I use real R2 buckets for local development?

**A:** Yes, but not recommended. Use Miniflare for local development:
```bash
# Local development (recommended)
just r2:test dev
wrangler dev --local

# Real R2 for development (not recommended)
wrangler dev --remote
```

### Q: How do I migrate from the old R2 system?

**A:** See the [Migration Guide](migration-guide.md) for step-by-step instructions.

### Q: Can I use multiple Cloudflare accounts?

**A:** Yes, configure different environments:
```bash
# Account A (production)
just secrets:edit secrets/r2-prod.yaml

# Account B (development)
just secrets:edit secrets/r2-dev.yaml
```

### Q: How do I backup my R2 data?

**A:** Use the AWS SDK to copy between buckets:
```typescript
// Copy to backup bucket
await r2Client.send(new CopyObjectCommand({
  Bucket: 'backup-bucket',
  Key: key,
  CopySource: `production-bucket/${key}`
}));
```

### Q: What's the difference between Workers binding and S3 API?

**A:**
- **Workers binding**: Direct R2 access within Workers, better performance
- **S3 API**: Standard S3 interface, works with existing S3 tools

### Q: How do I handle large file uploads?

**A:** Use multipart upload:
```typescript
// For files > 5MB, use multipart upload
if (fileSize > 5 * 1024 * 1024) {
  return await multipartUpload(bucket, key, data);
}
```

## 🆘 Getting More Help

### System Information for Support

When reporting issues, include:

```bash
# System information
echo "=== System Info ==="
uname -a
node --version
nix --version

echo "=== R2 System Status ==="
just status

echo "=== Configuration Status ==="
just r2:validate-all

echo "=== Recent Logs ==="
wrangler tail --lines 50
```

### Resources

- **[Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)**
- **[Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)**
- **[AWS SDK v3 Documentation](https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/)**
- **[Miniflare Documentation](https://miniflare.dev/)**

### Report Issues

1. Check this troubleshooting guide first
2. Search existing issues in the repository
3. Include system information and error logs
4. Provide minimal reproduction steps