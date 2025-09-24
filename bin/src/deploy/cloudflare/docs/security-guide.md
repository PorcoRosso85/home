# 🔒 Security Best Practices Guide

Comprehensive security guide for the R2 Connection Management System covering encryption, access control, and security monitoring.

## 🎯 Security Overview

This system implements multiple layers of security:

- **🔐 Secret Encryption**: SOPS with Age encryption for all sensitive data
- **📋 Plaintext Detection**: Automatic scanning for exposed credentials
- **🛡️ Schema Validation**: TypeScript and JSON Schema validation
- **🔍 Access Control**: Fine-grained permissions and CORS configuration
- **📊 Security Monitoring**: Audit logging and security metrics

## 🔐 Secret Management

### 1. SOPS Encryption Setup

**Initialize Age Encryption:**
```bash
# Generate Age key pair
just secrets:init

# This creates:
# - Private key: ~/.config/sops/age/keys.txt
# - Public key: Added to .sops.yaml
```

**Age Key Security:**
```bash
# Secure the private key
chmod 600 ~/.config/sops/age/keys.txt

# Backup your Age key securely
cp ~/.config/sops/age/keys.txt ~/backup/age-key-$(date +%Y%m%d).txt

# Never commit the private key to git
echo "~/.config/sops/age/keys.txt" >> ~/.gitignore
```

### 2. Secret Storage Best Practices

**✅ DO:**
- Use encrypted `secrets/r2.yaml` for all credentials
- Rotate credentials regularly (monthly recommended)
- Use unique credentials per environment
- Store backup Age keys in secure password manager
- Use strong, randomly generated access keys

**❌ DON'T:**
- Store credentials in environment variables
- Commit plaintext secrets to git
- Share credentials via chat/email
- Use the same credentials across environments
- Use weak or predictable passwords

### 3. Secret Rotation

```bash
# Regular rotation process (monthly)

# 1. Generate new R2 credentials in Cloudflare Dashboard
# 2. Update encrypted secrets
just secrets:edit secrets/r2.yaml

# 3. Test new credentials
just r2:validate prod

# 4. Deploy with new credentials
just r2:deploy-prep prod
wrangler deploy

# 5. Revoke old credentials in Cloudflare Dashboard
```

### 4. Multi-Environment Secret Management

```yaml
# secrets/r2-prod.yaml (Production)
cf_account_id: "prod-account-id"
r2_credentials:
  access_key_id: "PROD_ACCESS_KEY"
  secret_access_key: "PROD_SECRET_KEY"
security:
  require_auth: true
  rate_limiting: true
  encryption_at_rest: true

# secrets/r2-stg.yaml (Staging)
cf_account_id: "staging-account-id"
r2_credentials:
  access_key_id: "STG_ACCESS_KEY"
  secret_access_key: "STG_SECRET_KEY"
security:
  require_auth: true
  rate_limiting: false  # Relaxed for testing
  encryption_at_rest: true
```

## 🛡️ Access Control

### 1. Cloudflare API Token Security

**Principle of Least Privilege:**
```bash
# Create role-specific tokens

# For deployment (Workers:Edit)
curl -X POST "https://api.cloudflare.com/client/v4/user/tokens" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "Workers Deploy Token",
    "policies": [
      {
        "effect": "allow",
        "permission_groups": [
          {"id": "zone:zone:read"},
          {"id": "zone:worker:edit"}
        ],
        "resources": {
          "com.cloudflare.api.account.zone.*": "*"
        }
      }
    ]
  }'

# For R2 operations only (R2:Edit)
curl -X POST "https://api.cloudflare.com/client/v4/user/tokens" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "R2 Operations Token",
    "policies": [
      {
        "effect": "allow",
        "permission_groups": [
          {"id": "account:r2:edit"}
        ],
        "resources": {
          "com.cloudflare.api.account.*": "*"
        }
      }
    ]
  }'
```

**Token Management:**
```bash
# List active tokens
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# Verify token permissions
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $TOKEN_TO_VERIFY"

# Revoke unused tokens
curl -X DELETE "https://api.cloudflare.com/client/v4/user/tokens/$TOKEN_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

### 2. R2 Bucket Security

**Bucket-Level Permissions:**
```yaml
# In secrets/r2.yaml
r2_buckets:
  # Private bucket - sensitive data
  - name: "user-documents"
    public_access: false
    cors_origins:
      - "https://yourdomain.com"    # Specific domain only
    security:
      require_auth: true
      encryption_at_rest: true

  # Public bucket - static assets with restrictions
  - name: "static-assets"
    public_access: true
    custom_domain: "cdn.yourdomain.com"
    cors_origins:
      - "https://yourdomain.com"
      - "https://app.yourdomain.com"
    security:
      rate_limiting: true           # Prevent abuse
      max_file_size: 10485760      # 10MB limit
```

**Access Control in Workers:**
```typescript
// Implement authentication middleware
async function authenticateRequest(request: Request): Promise<string | null> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return null;
  }

  const token = authHeader.substring(7);

  // Validate JWT token
  try {
    const payload = await verifyJWT(token, JWT_SECRET);
    return payload.userId;
  } catch (error) {
    return null;
  }
}

// Protect R2 operations
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Authenticate user
    const userId = await authenticateRequest(request);
    if (!userId) {
      return new Response('Unauthorized', { status: 401 });
    }

    // Authorize R2 access based on user
    const url = new URL(request.url);
    const objectKey = url.pathname.substring(1);

    if (!await isUserAuthorizedForObject(userId, objectKey)) {
      return new Response('Forbidden', { status: 403 });
    }

    // Proceed with R2 operation
    return handleR2Request(request, env);
  }
};
```

### 3. CORS Security

**Strict CORS Configuration:**
```typescript
// Define allowed origins per environment
const ALLOWED_ORIGINS = {
  production: ['https://yourdomain.com'],
  staging: ['https://staging.yourdomain.com', 'https://localhost:3000'],
  development: ['http://localhost:3000', 'http://localhost:8787']
};

function validateOrigin(request: Request, environment: string): boolean {
  const origin = request.headers.get('Origin');
  if (!origin) return false;

  const allowedOrigins = ALLOWED_ORIGINS[environment] || [];
  return allowedOrigins.includes(origin);
}

// Apply CORS headers
function corsHeaders(origin: string) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400', // 24 hours
  };
}
```

## 🔍 Security Monitoring

### 1. Plaintext Secret Detection

**Automated Detection:**
```bash
# Run security checks
just secrets:check

# This scans for patterns like:
# - AWS Access Keys: AKIA[A-Z0-9]{16}
# - Stripe Keys: sk_live_[a-zA-Z0-9]{24,}
# - GitHub Tokens: ghp_[a-zA-Z0-9]{36}
# - Custom patterns defined in security policy
```

**Custom Pattern Detection:**
```bash
# Add custom patterns to flake.nix
# In the security check configuration:
patterns = [
  "AKIA[A-Z0-9]{16}"                    # AWS Access Key
  "sk_live_[a-zA-Z0-9]{24,}"           # Stripe Live Key
  "ghp_[a-zA-Z0-9]{36}"                # GitHub Personal Access Token
  "cf_[a-zA-Z0-9]{32}"                 # Custom Cloudflare token pattern
];
```

### 2. Access Logging

**Worker-Level Logging:**
```typescript
interface SecurityEvent {
  timestamp: string;
  eventType: 'auth_success' | 'auth_failure' | 'access_denied' | 'r2_operation';
  userId?: string;
  ip: string;
  userAgent: string;
  resource: string;
  outcome: 'success' | 'failure';
  details?: Record<string, any>;
}

async function logSecurityEvent(event: SecurityEvent, env: Env) {
  // Log to analytics engine
  env.ANALYTICS.writeDataPoint({
    ...event,
    timestamp: new Date().toISOString()
  });

  // For critical events, also log to external service
  if (event.eventType === 'auth_failure' || event.outcome === 'failure') {
    await fetch('https://your-siem.com/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event)
    });
  }
}

// Usage in Worker
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const startTime = Date.now();
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const userAgent = request.headers.get('User-Agent') || 'unknown';

    try {
      const userId = await authenticateRequest(request);

      if (!userId) {
        await logSecurityEvent({
          timestamp: new Date().toISOString(),
          eventType: 'auth_failure',
          ip,
          userAgent,
          resource: new URL(request.url).pathname,
          outcome: 'failure'
        }, env);

        return new Response('Unauthorized', { status: 401 });
      }

      // Log successful authentication
      await logSecurityEvent({
        timestamp: new Date().toISOString(),
        eventType: 'auth_success',
        userId,
        ip,
        userAgent,
        resource: new URL(request.url).pathname,
        outcome: 'success'
      }, env);

      return await handleRequest(request, env, userId);

    } catch (error) {
      await logSecurityEvent({
        timestamp: new Date().toISOString(),
        eventType: 'r2_operation',
        ip,
        userAgent,
        resource: new URL(request.url).pathname,
        outcome: 'failure',
        details: { error: error.message }
      }, env);

      throw error;
    }
  }
};
```

### 3. Rate Limiting

**Worker-Level Rate Limiting:**
```typescript
interface RateLimitConfig {
  windowMs: number;     // Time window in milliseconds
  maxRequests: number;  // Max requests per window
  skipSuccessfulRequests?: boolean;
}

class RateLimiter {
  constructor(
    private kv: KVNamespace,
    private config: RateLimitConfig
  ) {}

  async isRateLimited(key: string): Promise<boolean> {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;

    // Get current request count
    const countStr = await this.kv.get(`rate_limit:${key}`);
    const requests = countStr ? JSON.parse(countStr) : [];

    // Remove expired requests
    const validRequests = requests.filter((timestamp: number) => timestamp > windowStart);

    // Check if limit exceeded
    if (validRequests.length >= this.config.maxRequests) {
      return true;
    }

    // Add current request
    validRequests.push(now);
    await this.kv.put(
      `rate_limit:${key}`,
      JSON.stringify(validRequests),
      { expirationTtl: Math.ceil(this.config.windowMs / 1000) }
    );

    return false;
  }
}

// Usage
const rateLimiter = new RateLimiter(env.RATE_LIMIT_KV, {
  windowMs: 60 * 1000,    // 1 minute
  maxRequests: 100        // 100 requests per minute
});

const clientId = request.headers.get('CF-Connecting-IP') || 'unknown';
if (await rateLimiter.isRateLimited(clientId)) {
  return new Response('Rate limit exceeded', { status: 429 });
}
```

## 🔐 Encryption

### 1. Data at Rest

**R2 Bucket Encryption:**
```yaml
# In secrets/r2.yaml
r2_buckets:
  - name: "sensitive-data"
    security:
      encryption_at_rest: true      # Enable R2 encryption
      encryption_key_rotation: true # Enable key rotation
```

**Application-Level Encryption:**
```typescript
import { webcrypto } from 'crypto';

class DataEncryption {
  private static async deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
    const encoder = new TextEncoder();
    const baseKey = await webcrypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    return await webcrypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      baseKey,
      {
        name: 'AES-GCM',
        length: 256
      },
      false,
      ['encrypt', 'decrypt']
    );
  }

  static async encrypt(data: string, password: string): Promise<string> {
    const encoder = new TextEncoder();
    const salt = webcrypto.getRandomValues(new Uint8Array(16));
    const iv = webcrypto.getRandomValues(new Uint8Array(12));

    const key = await this.deriveKey(password, salt);
    const encrypted = await webcrypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encoder.encode(data)
    );

    // Combine salt + iv + encrypted data
    const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
    combined.set(salt, 0);
    combined.set(iv, salt.length);
    combined.set(new Uint8Array(encrypted), salt.length + iv.length);

    return btoa(String.fromCharCode(...combined));
  }

  static async decrypt(encryptedData: string, password: string): Promise<string> {
    const combined = new Uint8Array(
      atob(encryptedData).split('').map(char => char.charCodeAt(0))
    );

    const salt = combined.slice(0, 16);
    const iv = combined.slice(16, 28);
    const encrypted = combined.slice(28);

    const key = await this.deriveKey(password, salt);
    const decrypted = await webcrypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      encrypted
    );

    return new TextDecoder().decode(decrypted);
  }
}

// Usage for sensitive R2 data
async function uploadSensitiveData(bucket: R2Bucket, key: string, data: string) {
  const encryptionKey = env.DATA_ENCRYPTION_KEY; // From encrypted secrets
  const encryptedData = await DataEncryption.encrypt(data, encryptionKey);

  return await bucket.put(key, encryptedData, {
    customMetadata: {
      encrypted: 'true',
      algorithm: 'AES-GCM-256'
    }
  });
}
```

### 2. Data in Transit

**TLS Configuration:**
```typescript
// Ensure all R2 connections use HTTPS
const r2Client = new S3Client({
  region: 'auto',
  endpoint: 'https://account-id.r2.cloudflarestorage.com', // HTTPS only
  credentials: R2_CREDENTIALS,
  forcePathStyle: true
});

// For Worker fetch requests
async function secureR2Request(url: string, options: RequestInit) {
  // Ensure HTTPS
  if (!url.startsWith('https://')) {
    throw new Error('Only HTTPS connections allowed');
  }

  // Add security headers
  const headers = {
    ...options.headers,
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY'
  };

  return await fetch(url, { ...options, headers });
}
```

## 🚨 Incident Response

### 1. Security Incident Procedures

**Immediate Response:**
```bash
# 1. Revoke compromised credentials immediately
# In Cloudflare Dashboard:
# - API Tokens → Revoke token
# - R2 → API tokens → Revoke R2 credentials

# 2. Generate new credentials
just secrets:edit secrets/r2.yaml
# Update with new credentials

# 3. Deploy with new credentials
just r2:deploy-prep prod
wrangler deploy

# 4. Audit access logs
wrangler tail --filter error --lines 1000
```

**Investigation:**
```bash
# Check for unauthorized access
curl -X GET "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/audit_logs" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json"

# Check R2 access logs (if configured)
# Review CloudFlare Analytics for unusual patterns
```

### 2. Recovery Procedures

**Credential Compromise:**
```bash
# 1. Immediate credential rotation
just secrets:edit secrets/r2.yaml

# 2. Update all environments
for env in dev stg prod; do
  just r2:gen-config $env
  # Deploy to each environment
done

# 3. Verify security
just secrets:check
just r2:validate-all
```

**Data Breach Response:**
```bash
# 1. Identify affected buckets/objects
wrangler r2 object list bucket-name --prefix sensitive/

# 2. Change access controls
# Update bucket configurations to private
just secrets:edit secrets/r2.yaml

# 3. Audit and notify stakeholders
# Generate access report
```

## 📋 Security Checklist

### Daily Security Tasks
- [ ] Monitor security alerts and logs
- [ ] Review failed authentication attempts
- [ ] Check for unusual R2 usage patterns

### Weekly Security Tasks
- [ ] Run plaintext secret detection: `just secrets:check`
- [ ] Review API token usage and permissions
- [ ] Audit user access and permissions
- [ ] Check for security updates

### Monthly Security Tasks
- [ ] Rotate R2 credentials
- [ ] Rotate API tokens
- [ ] Review and update CORS policies
- [ ] Security audit of configurations
- [ ] Update security documentation

### Quarterly Security Tasks
- [ ] Comprehensive security review
- [ ] Penetration testing (if applicable)
- [ ] Update security policies
- [ ] Staff security training
- [ ] Disaster recovery testing

## 🔧 Security Tools Integration

### 1. External Security Scanners

**Integration with GitGuardian:**
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: GitGuardian scan
        uses: GitGuardian/ggshield-action@v1
        env:
          GITGUARDIAN_API_KEY: ${{ secrets.GITGUARDIAN_API_KEY }}
```

**Integration with Snyk:**
```bash
# Install Snyk CLI
npm install -g snyk

# Scan for vulnerabilities
snyk test
snyk monitor

# Scan infrastructure as code
snyk iac test
```

### 2. SIEM Integration

**Log Forwarding:**
```typescript
// Forward security events to SIEM
async function forwardToSIEM(event: SecurityEvent) {
  await fetch('https://your-siem.com/api/events', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SIEM_API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ...event,
      source: 'cloudflare-r2-system',
      timestamp: new Date().toISOString()
    })
  });
}
```

## 📚 Security Standards Compliance

### 1. SOC 2 Type II Considerations

**Access Controls:**
- Implement principle of least privilege
- Regular access reviews and audits
- Multi-factor authentication for admin access

**Data Encryption:**
- Encryption at rest and in transit
- Key management and rotation
- Secure key storage

**Monitoring:**
- Comprehensive logging and monitoring
- Security incident response procedures
- Regular security assessments

### 2. GDPR Compliance

**Data Protection:**
```typescript
// Implement right to erasure
async function deleteUserData(userId: string, bucket: R2Bucket) {
  const objects = await bucket.list({ prefix: `users/${userId}/` });

  for (const object of objects.objects) {
    await bucket.delete(object.key);
  }

  // Log the deletion for audit
  await logSecurityEvent({
    eventType: 'data_deletion',
    userId,
    resource: `users/${userId}`,
    outcome: 'success',
    details: { reason: 'gdpr_request' }
  });
}
```

**Data Minimization:**
```typescript
// Only store necessary data
interface UserData {
  id: string;
  email: string;        // Required for communication
  preferences: object;  // Required for service
  // Avoid storing unnecessary PII
}
```

## 🆘 Security Contact Information

For security-related issues:

1. **Internal Security Team**: security@yourcompany.com
2. **Cloudflare Security**: security@cloudflare.com
3. **Emergency Procedures**: Follow incident response plan

## 📚 Additional Security Resources

- **[Cloudflare Security Documentation](https://developers.cloudflare.com/fundamentals/security/)**
- **[OWASP Top 10](https://owasp.org/www-project-top-ten/)**
- **[NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)**
- **[SOC 2 Compliance Guide](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)**