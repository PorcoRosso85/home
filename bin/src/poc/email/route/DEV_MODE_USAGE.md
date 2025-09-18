# Development Mode Configuration

## Overview
The wrangler.toml has been updated to support development mode with HTTP endpoints for local testing of the email archive worker.

## Key Changes Made

### 1. Environment-Specific Configuration
- **Development Environment**: Uses `src/dev/email-endpoint.js` as the main entry point
- **Production Environment**: Uses `src/index.js` (standard email worker)

### 2. Development-Specific Features
- **HTTP Endpoints**: `/__email` and `/__health` endpoints available in dev mode
- **Extended Timeout**: 60 seconds (vs 30 seconds in production) for debugging
- **Default MinIO Credentials**: Automatically configured for local development

### 3. Environment Variables Added
- `DEV_MODE`: Boolean flag to distinguish development from production
- `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`: Included in development environment

## Usage

### Start Development Server
```bash
wrangler dev --env development
```

### Test Email Processing
```bash
# Using structured JSON data
curl -X POST http://localhost:8787/__email \
  -H "Content-Type: application/json" \
  -d '{
    "from": "sender@example.com",
    "to": "recipient@example.com", 
    "subject": "Test Email",
    "content": "This is a test email from dev mode."
  }'

# Using raw email content
curl -X POST http://localhost:8787/__email \
  -H "Content-Type: text/plain" \
  -d "From: sender@example.com
To: recipient@example.com
Subject: Test Email

This is a test email body."
```

### Health Check
```bash
curl http://localhost:8787/__health
```

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Entry Point | `src/dev/email-endpoint.js` | `src/index.js` |
| HTTP Endpoints | Available (`/__email`, `/__health`) | Basic response only |
| Timeout | 60 seconds | 30 seconds |
| MinIO Credentials | Auto-configured | Must be set as secrets |
| Email Routing | Same (configured for both) | Same |

## Next Steps
1. Start MinIO server: `./setup-minio.sh`
2. Start development server: `wrangler dev --env development`
3. Test endpoints using the curl commands above
4. Check MinIO console at http://localhost:9001 to verify archived emails