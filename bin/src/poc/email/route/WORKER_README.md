# Email Archive Worker Implementation

## Overview

This Cloudflare Worker implementation provides automatic email archiving to MinIO S3-compatible storage. It intercepts incoming emails via Cloudflare Email Routing and stores both the raw email content and extracted metadata.

## Files Structure

```
src/
├── index.js          # Main worker implementation
├── types.d.ts        # TypeScript definitions
package.json          # Dependencies and scripts
wrangler.toml         # Worker configuration
```

## Key Features

### 1. Email Processing
- **Raw Email Storage**: Preserves original `.eml` format
- **Metadata Extraction**: Comprehensive header and content analysis
- **Attachment Detection**: Identifies multipart content and attachments
- **Message ID Generation**: Creates unique IDs for emails missing them

### 2. S3 Storage Integration
- **MinIO Compatibility**: Uses AWS SDK with MinIO-specific configuration
- **Hierarchical Organization**: `emails/YYYY/MM/DD/message-id` structure
- **Dual Storage**: Separate `.eml` and `.json` files for each email
- **Parallel Operations**: Concurrent storage of email and metadata

### 3. Error Handling
- **Comprehensive Logging**: Detailed processing information
- **Graceful Degradation**: Continues processing even with non-critical errors
- **Processing Time Tracking**: Performance monitoring
- **Non-Blocking Errors**: Prevents email bounce-back on archive failures

## Configuration

### Environment Variables
```
MINIO_ENDPOINT=http://localhost:9000  # MinIO server URL
MINIO_ACCESS_KEY=minioadmin           # Access credentials
MINIO_SECRET_KEY=minioadmin           # Secret credentials
BUCKET_NAME=email-archive             # Target bucket name
```

### Wrangler Configuration
The `wrangler.toml` includes:
- Email routing rules for all incoming messages
- Development and production environment settings
- Resource limits (30-second timeout)
- Node.js compatibility mode

## Storage Format

### Email Files (.eml)
- Content-Type: `message/rfc822`
- Contains complete original email with headers
- Preserves all MIME parts and attachments

### Metadata Files (.json)
```json
{
  "messageId": "clean-message-id",
  "originalMessageId": "<original@domain.com>",
  "receivedAt": "2024-01-15T10:30:00.000Z",
  "emailDate": "2024-01-15T10:25:00.000Z",
  "from": "sender@example.com",
  "to": ["recipient@domain.com"],
  "subject": "Email Subject",
  "size": 12345,
  "contentType": "multipart/mixed",
  "isMultipart": true,
  "headers": {
    "message-id": "<original@domain.com>",
    "date": "Mon, 15 Jan 2024 10:25:00 +0000",
    "subject": "Email Subject"
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "contentType": "application/octet-stream",
      "detectedAt": "2024-01-15T10:30:00.000Z"
    }
  ],
  "archivedBy": "email-archive-worker",
  "workerVersion": "1.0.0"
}
```

## Usage

### Development
```bash
# Install dependencies
npm install

# Start local development
npm run dev

# Start MinIO server (separate terminal)
nix run .#start-minio

# Setup bucket
nix run .#setup-bucket
```

### Deployment
```bash
# Set secrets
wrangler secret put MINIO_ACCESS_KEY
wrangler secret put MINIO_SECRET_KEY

# Deploy worker
npm run deploy
```

### Testing
```bash
# Run development server
npm run dev

# Test archiving (separate terminal)
nix run .#test-archive
```

## Security Considerations

1. **Credentials Management**: Use Wrangler secrets for production credentials
2. **MinIO Access**: Configure appropriate bucket policies and IAM
3. **Email Privacy**: Ensure compliance with data protection regulations
4. **Storage Encryption**: Enable MinIO server-side encryption
5. **Network Security**: Use HTTPS for production MinIO endpoints

## Performance Characteristics

- **Processing Time**: ~100-500ms per email depending on size
- **Concurrent Operations**: Parallel storage of .eml and .json files
- **Memory Efficiency**: Streams large emails without full memory load
- **Storage Efficiency**: Hierarchical organization for easy retrieval

## Error Recovery

The worker implements several error recovery mechanisms:
- Automatic message ID generation for malformed emails
- Graceful handling of metadata extraction failures
- Non-blocking error responses to prevent email bounces
- Comprehensive error logging for debugging

## Integration Points

### Cloudflare Email Routing
Configure routing rules to send all emails to this worker:
```toml
[[email_routing_rules]]
type = "all"
actions = [
  { type = "worker", value = "email-archive-worker" }
]
```

### MinIO Setup
Required bucket configuration:
- Bucket name: `email-archive`
- Access policy: Worker-only read/write
- Versioning: Optional but recommended
- Lifecycle policies: Configure based on retention requirements

## Monitoring

The worker provides extensive logging:
- Email processing start/completion times
- Storage operation success/failure
- Metadata extraction warnings
- Performance metrics

Monitor via Cloudflare Workers dashboard or external log aggregation services.