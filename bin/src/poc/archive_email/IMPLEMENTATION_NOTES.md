# Email Archive Implementation Notes

## System Architecture Overview

The email archiving system follows a single-responsibility principle: **archive all incoming emails to local S3 storage**.

### Components

1. **Cloudflare Email Routing**
   - Receives emails for configured domains
   - Routes to Worker for processing
   - Also delivers to regular inbox (non-blocking)

2. **Cloudflare Worker**
   - Handles email reception events
   - Extracts metadata and raw email content
   - Stores to MinIO via S3 API
   - Implements retry logic for resilience

3. **MinIO (Local S3)**
   - Provides S3-compatible API locally
   - Stores email data with hierarchical structure
   - Enables data sovereignty and local control

## Technical Implementation Details

### Worker Environment Variables

```javascript
// Required environment variables
const ENV_VARS = {
  MINIO_ENDPOINT: 'https://minio.example.com',
  MINIO_ACCESS_KEY: 'your-access-key',
  MINIO_SECRET_KEY: 'your-secret-key',
  BUCKET_NAME: 'email-archive',
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY_MS: 1000
};
```

### Error Handling Strategy

```javascript
async function archiveWithRetry(email, env, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await archiveEmail(email, env);
    } catch (error) {
      if (attempt === retries) {
        // Log to external monitoring
        await logError(error, email.messageId);
        throw error;
      }
      // Exponential backoff
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

### Data Storage Pattern

```
email-archive/
├── emails/
│   ├── 2024/01/15/{messageId}.eml     # Raw RFC822 email
│   ├── 2024/01/15/{messageId}.json    # Metadata
│   └── 2024/01/15/{messageId}/        # Attachments (future)
├── indexes/
│   ├── by-sender/                      # Future: sender index
│   ├── by-date/                        # Future: date index
│   └── by-subject/                     # Future: subject index
└── lifecycle/
    └── retention-policy.json           # Retention rules
```

### Performance Considerations

1. **Parallel Processing**
   - Save .eml and .json files in parallel
   - Use Promise.all() for concurrent S3 operations

2. **Memory Management**
   - Stream large attachments directly to S3
   - Avoid loading entire email into memory for large messages

3. **Worker Limits**
   - 30-second execution limit (paid plan)
   - 128MB memory limit
   - Plan for graceful degradation

### Security Implementation

1. **Authentication**
   ```javascript
   // Use IAM-style authentication
   const s3Config = {
     endpoint: env.MINIO_ENDPOINT,
     credentials: {
       accessKeyId: env.MINIO_ACCESS_KEY,
       secretAccessKey: env.MINIO_SECRET_KEY
     },
     region: 'us-east-1', // MinIO default
     forcePathStyle: true  // Required for MinIO
   };
   ```

2. **Encryption**
   - Enable SSE-S3 on MinIO bucket
   - Use TLS for Worker-MinIO communication
   - Consider client-side encryption for sensitive data

3. **Access Control**
   - Worker service account with minimal permissions
   - Write-only access to archive bucket
   - Separate read access for search/retrieval systems

### Monitoring and Observability

```javascript
// Structured logging for monitoring
const logEntry = {
  timestamp: new Date().toISOString(),
  messageId: email.messageId,
  sender: email.from,
  size: email.size,
  processingTimeMs: endTime - startTime,
  status: 'success',
  bucketKey: objectKey
};

// Send to logging service
await env.LOGGER.log(JSON.stringify(logEntry));
```

### Development Workflow

1. **Local Testing**
   ```bash
   # Start MinIO locally
   docker-compose up -d minio
   
   # Configure bucket
   mc alias set local http://localhost:9000 admin miniopassword
   mc mb local/email-archive
   mc policy set writeonly local/email-archive
   ```

2. **Worker Development**
   ```bash
   # Use Wrangler for local development
   wrangler dev --local
   
   # Test with email simulator
   curl -X POST http://localhost:8787/__email \
     -H "Content-Type: message/rfc822" \
     --data-binary @test-email.eml
   ```

3. **Deployment**
   ```bash
   # Deploy to Cloudflare
   wrangler publish
   
   # Configure secrets
   wrangler secret put MINIO_ACCESS_KEY
   wrangler secret put MINIO_SECRET_KEY
   ```

### Edge Cases and Considerations

1. **Large Attachments**
   - Implement streaming for files > 10MB
   - Consider separate attachment storage strategy
   - Monitor Worker memory usage

2. **Duplicate Messages**
   - Use Message-ID as unique key
   - Implement idempotent operations
   - Skip if already exists in S3

3. **Malformed Emails**
   - Graceful handling of invalid RFC822 format
   - Store raw data even if parsing fails
   - Log parsing errors for investigation

### Future Enhancements

1. **Search Index**
   - Build inverted index for full-text search
   - Use separate index storage in S3
   - Consider Elasticsearch integration

2. **Compression**
   - Compress old emails (> 30 days)
   - Use S3 lifecycle policies
   - Maintain searchability

3. **Analytics**
   - Email volume trends
   - Sender/recipient statistics
   - Attachment type distribution

## Testing Strategy

### Unit Tests
```javascript
// Test email parsing
describe('Email Parser', () => {
  it('should extract metadata correctly', () => {
    const rawEmail = fs.readFileSync('test-email.eml');
    const metadata = parseEmail(rawEmail);
    expect(metadata.messageId).toBeDefined();
    expect(metadata.from).toMatch(/.*@.*/);
  });
});
```

### Integration Tests
```javascript
// Test S3 storage
describe('S3 Storage', () => {
  it('should store email successfully', async () => {
    const result = await storeEmail(testEmail, mockS3Client);
    expect(result.ETag).toBeDefined();
    expect(mockS3Client.putObject).toHaveBeenCalledTimes(2);
  });
});
```

### E2E Tests
- Send test emails through actual Email Routing
- Verify storage in MinIO
- Check metadata accuracy

## Operational Runbook

### Deployment Checklist
- [ ] MinIO bucket created and configured
- [ ] Worker environment variables set
- [ ] Email Routing rules configured
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented

### Troubleshooting Guide

1. **Worker Timeouts**
   - Check email size
   - Verify network connectivity to MinIO
   - Review Worker logs

2. **Storage Failures**
   - Verify MinIO health
   - Check bucket permissions
   - Monitor disk space

3. **Missing Emails**
   - Check Email Routing logs
   - Verify Worker invocation
   - Review error logs

### Maintenance Tasks

1. **Regular**
   - Monitor storage usage
   - Review error logs
   - Update Worker dependencies

2. **Periodic**
   - Test disaster recovery
   - Review retention policies
   - Performance optimization

## Cost Optimization

1. **Storage Tiering**
   - Hot: Recent 30 days (fast access)
   - Warm: 30-365 days (compressed)
   - Cold: > 1 year (archived)

2. **Worker Optimization**
   - Minimize execution time
   - Batch operations where possible
   - Use edge caching for static config

3. **Monitoring Costs**
   - Track Worker invocations
   - Monitor storage growth
   - Set up cost alerts