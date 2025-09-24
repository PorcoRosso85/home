# 🔧 AWS SDK v3 Integration Guide

Complete guide for using AWS SDK v3 with Cloudflare R2 through the S3-compatible API.

## 🎯 Overview

Cloudflare R2 provides an S3-compatible API, allowing you to use the AWS SDK v3 for S3 operations. This is useful for:

- **Legacy Integration**: Migrating existing AWS S3 code to R2
- **Multi-Cloud Strategy**: Using the same code for both S3 and R2
- **Advanced Features**: Accessing S3-specific features not available in Workers API
- **External Tools**: Using existing S3 tools and libraries

## 🏗️ Setup and Configuration

### 1. Install AWS SDK v3

```bash
# Install the S3 client
npm install @aws-sdk/client-s3

# Optional: Install additional utilities
npm install @aws-sdk/s3-request-presigner
npm install @aws-sdk/credential-providers
```

### 2. Configure R2 Connection

First, ensure you have R2 credentials configured:

```bash
# Set up encrypted secrets
just secrets:init
just secrets:edit secrets/r2.yaml
```

Your `secrets/r2.yaml` should include:

```yaml
r2_credentials:
  access_key_id: "your-r2-access-key-id"
  secret_access_key: "your-r2-secret-access-key"

# R2 endpoint configuration
cf_account_id: "your-account-id"
r2_endpoint: "https://your-account-id.r2.cloudflarestorage.com"
```

### 3. Generate Connection Manifest

```bash
# Generate R2 connection manifest
just r2:gen-manifest prod

# This creates: generated/r2-connection-manifest-prod.json
# Contains all connection details for external tools
```

## 💻 Basic AWS SDK v3 Configuration

### 1. Client Configuration

```typescript
import { S3Client } from '@aws-sdk/client-s3';

// Configure S3 client for R2
const r2Client = new S3Client({
  region: 'auto', // R2 uses 'auto' region
  endpoint: `https://${ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId: R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
  },
  // Important: Force path-style URLs for R2 compatibility
  forcePathStyle: true,
});
```

### 2. Environment-Based Configuration

```typescript
import { readFileSync } from 'fs';

// Load configuration from generated manifest
function loadR2Config(environment: string = 'prod') {
  const manifestPath = `generated/r2-connection-manifest-${environment}.json`;
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

  return new S3Client({
    region: manifest.region,
    endpoint: manifest.endpoint,
    credentials: manifest.credentials,
    forcePathStyle: true,
  });
}

const r2Client = loadR2Config('prod');
```

### 3. Configuration with Environment Variables

```typescript
// Use environment variables (from SOPS decryption)
const r2Client = new S3Client({
  region: process.env.R2_REGION || 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  },
  forcePathStyle: true,
});
```

## 🧪 Basic Operations

### 1. Bucket Operations

```typescript
import {
  ListBucketsCommand,
  CreateBucketCommand,
  DeleteBucketCommand,
  HeadBucketCommand
} from '@aws-sdk/client-s3';

// List all buckets
async function listBuckets() {
  const command = new ListBucketsCommand({});
  const response = await r2Client.send(command);
  return response.Buckets;
}

// Check if bucket exists
async function bucketExists(bucketName: string): Promise<boolean> {
  try {
    await r2Client.send(new HeadBucketCommand({ Bucket: bucketName }));
    return true;
  } catch (error) {
    if (error.name === 'NotFound') {
      return false;
    }
    throw error;
  }
}

// Create bucket (if you have permissions)
async function createBucket(bucketName: string) {
  const command = new CreateBucketCommand({ Bucket: bucketName });
  return await r2Client.send(command);
}
```

### 2. Object Operations

```typescript
import {
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand,
  HeadObjectCommand,
  ListObjectsV2Command
} from '@aws-sdk/client-s3';

// Upload an object
async function uploadObject(bucketName: string, key: string, body: string | Uint8Array) {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: key,
    Body: body,
    // Optional: Add metadata
    Metadata: {
      uploadedAt: new Date().toISOString(),
      environment: 'production'
    },
    // Optional: Set content type
    ContentType: 'application/json'
  });

  return await r2Client.send(command);
}

// Download an object
async function downloadObject(bucketName: string, key: string) {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  const response = await r2Client.send(command);

  // Convert stream to string
  const body = await response.Body?.transformToString();
  return {
    body,
    metadata: response.Metadata,
    contentType: response.ContentType,
    lastModified: response.LastModified
  };
}

// Get object metadata only
async function getObjectMetadata(bucketName: string, key: string) {
  const command = new HeadObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  return await r2Client.send(command);
}

// List objects in bucket
async function listObjects(bucketName: string, prefix?: string) {
  const command = new ListObjectsV2Command({
    Bucket: bucketName,
    Prefix: prefix,
    MaxKeys: 1000
  });

  const response = await r2Client.send(command);
  return response.Contents || [];
}

// Delete an object
async function deleteObject(bucketName: string, key: string) {
  const command = new DeleteObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  return await r2Client.send(command);
}
```

## 🔗 Advanced Features

### 1. Presigned URLs

```typescript
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';

// Generate presigned URL for download
async function generateDownloadUrl(bucketName: string, key: string, expiresIn: number = 3600) {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  return await getSignedUrl(r2Client, command, {
    expiresIn // seconds
  });
}

// Generate presigned URL for upload
async function generateUploadUrl(bucketName: string, key: string, contentType?: string) {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: key,
    ContentType: contentType
  });

  return await getSignedUrl(r2Client, command, {
    expiresIn: 3600 // 1 hour
  });
}

// Usage example
const downloadUrl = await generateDownloadUrl('my-bucket', 'document.pdf');
const uploadUrl = await generateUploadUrl('my-bucket', 'upload.jpg', 'image/jpeg');
```

### 2. Multipart Upload

```typescript
import {
  CreateMultipartUploadCommand,
  UploadPartCommand,
  CompleteMultipartUploadCommand,
  AbortMultipartUploadCommand
} from '@aws-sdk/client-s3';

async function multipartUpload(bucketName: string, key: string, data: Buffer) {
  const PART_SIZE = 5 * 1024 * 1024; // 5MB parts

  // Start multipart upload
  const createCommand = new CreateMultipartUploadCommand({
    Bucket: bucketName,
    Key: key
  });
  const { UploadId } = await r2Client.send(createCommand);

  if (!UploadId) {
    throw new Error('Failed to create multipart upload');
  }

  try {
    const parts = [];
    let partNumber = 1;

    // Upload parts
    for (let i = 0; i < data.length; i += PART_SIZE) {
      const end = Math.min(i + PART_SIZE, data.length);
      const partData = data.slice(i, end);

      const uploadCommand = new UploadPartCommand({
        Bucket: bucketName,
        Key: key,
        PartNumber: partNumber,
        UploadId,
        Body: partData
      });

      const response = await r2Client.send(uploadCommand);
      parts.push({
        ETag: response.ETag,
        PartNumber: partNumber
      });

      partNumber++;
    }

    // Complete multipart upload
    const completeCommand = new CompleteMultipartUploadCommand({
      Bucket: bucketName,
      Key: key,
      UploadId,
      MultipartUpload: { Parts: parts }
    });

    return await r2Client.send(completeCommand);

  } catch (error) {
    // Abort multipart upload on error
    await r2Client.send(new AbortMultipartUploadCommand({
      Bucket: bucketName,
      Key: key,
      UploadId
    }));
    throw error;
  }
}
```

### 3. Batch Operations

```typescript
import { DeleteObjectsCommand } from '@aws-sdk/client-s3';

// Delete multiple objects at once
async function deleteMultipleObjects(bucketName: string, keys: string[]) {
  const command = new DeleteObjectsCommand({
    Bucket: bucketName,
    Delete: {
      Objects: keys.map(key => ({ Key: key })),
      Quiet: false // Set to true to suppress response details
    }
  });

  return await r2Client.send(command);
}

// Copy objects between buckets
async function copyObjects(sourceBucket: string, targetBucket: string, keys: string[]) {
  const promises = keys.map(async (key) => {
    const copyCommand = new CopyObjectCommand({
      Bucket: targetBucket,
      Key: key,
      CopySource: `${sourceBucket}/${key}`
    });
    return r2Client.send(copyCommand);
  });

  return await Promise.all(promises);
}
```

## 🌐 Integration Examples

### 1. Express.js API

```typescript
import express from 'express';
import multer from 'multer';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// Configure R2 client
const r2Client = loadR2Config();

// Upload endpoint
app.post('/upload', upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }

  try {
    const key = `uploads/${Date.now()}-${req.file.originalname}`;

    await r2Client.send(new PutObjectCommand({
      Bucket: 'my-uploads-bucket',
      Key: key,
      Body: req.file.buffer,
      ContentType: req.file.mimetype,
      Metadata: {
        originalName: req.file.originalname,
        uploadedAt: new Date().toISOString()
      }
    }));

    res.json({
      message: 'File uploaded successfully',
      key: key,
      url: `https://my-bucket.r2.dev/${key}` // If bucket is public
    });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});

// Download endpoint
app.get('/download/:key', async (req, res) => {
  try {
    const downloadUrl = await generateDownloadUrl('my-uploads-bucket', req.params.key);
    res.redirect(downloadUrl);
  } catch (error) {
    res.status(404).json({ error: 'File not found' });
  }
});
```

### 2. Next.js API Routes

```typescript
// pages/api/upload.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import formidable from 'formidable';
import fs from 'fs';

const r2Client = loadR2Config();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const form = formidable();
  const [fields, files] = await form.parse(req);

  const file = Array.isArray(files.file) ? files.file[0] : files.file;
  if (!file) {
    return res.status(400).json({ error: 'No file provided' });
  }

  try {
    const fileContent = fs.readFileSync(file.filepath);
    const key = `uploads/${Date.now()}-${file.originalFilename}`;

    await r2Client.send(new PutObjectCommand({
      Bucket: process.env.R2_BUCKET_NAME!,
      Key: key,
      Body: fileContent,
      ContentType: file.mimetype || 'application/octet-stream'
    }));

    res.json({ success: true, key });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};
```

### 3. Streaming Large Files

```typescript
import { Readable } from 'stream';

// Stream upload for large files
async function streamUpload(bucketName: string, key: string, stream: Readable) {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: key,
    Body: stream
  });

  return await r2Client.send(command);
}

// Stream download
async function streamDownload(bucketName: string, key: string): Promise<Readable> {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  const response = await r2Client.send(command);
  return response.Body as Readable;
}

// Example: Pipe file directly to R2
import { createReadStream } from 'fs';

const fileStream = createReadStream('large-file.zip');
await streamUpload('my-bucket', 'large-file.zip', fileStream);
```

## 🔧 Configuration Management

### 1. Environment-Specific Clients

```typescript
class R2ClientManager {
  private clients: Map<string, S3Client> = new Map();

  getClient(environment: string = 'prod'): S3Client {
    if (!this.clients.has(environment)) {
      const config = this.loadConfig(environment);
      const client = new S3Client({
        region: config.region,
        endpoint: config.endpoint,
        credentials: config.credentials,
        forcePathStyle: true
      });
      this.clients.set(environment, client);
    }

    return this.clients.get(environment)!;
  }

  private loadConfig(environment: string) {
    const manifestPath = `generated/r2-connection-manifest-${environment}.json`;
    return JSON.parse(readFileSync(manifestPath, 'utf8'));
  }
}

// Usage
const clientManager = new R2ClientManager();
const prodClient = clientManager.getClient('prod');
const stagingClient = clientManager.getClient('stg');
```

### 2. Configuration Validation

```typescript
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

// Load and validate R2 manifest schema
function validateR2Config(config: any): boolean {
  const ajv = new Ajv();
  addFormats(ajv);

  // Load schema from schemas/r2-manifest.json
  const schema = JSON.parse(readFileSync('schemas/r2-manifest.json', 'utf8'));
  const validate = ajv.compile(schema);

  const valid = validate(config);
  if (!valid) {
    console.error('Config validation errors:', validate.errors);
    return false;
  }

  return true;
}

// Use with config loading
function loadValidatedConfig(environment: string) {
  const config = JSON.parse(
    readFileSync(`generated/r2-connection-manifest-${environment}.json`, 'utf8')
  );

  if (!validateR2Config(config)) {
    throw new Error(`Invalid R2 configuration for environment: ${environment}`);
  }

  return config;
}
```

## 🧪 Testing with AWS SDK

### 1. Unit Testing

```typescript
// test/r2-operations.test.ts
import { jest } from '@jest/globals';
import { S3Client } from '@aws-sdk/client-s3';
import { mockClient } from 'aws-sdk-client-mock';

const s3Mock = mockClient(S3Client);

describe('R2 Operations', () => {
  beforeEach(() => {
    s3Mock.reset();
  });

  it('should upload object successfully', async () => {
    s3Mock.on(PutObjectCommand).resolves({
      ETag: '"mock-etag"',
      VersionId: 'mock-version'
    });

    const result = await uploadObject('test-bucket', 'test-key', 'test data');
    expect(result.ETag).toBe('"mock-etag"');
  });

  it('should handle upload errors', async () => {
    s3Mock.on(PutObjectCommand).rejects(new Error('Network error'));

    await expect(uploadObject('test-bucket', 'test-key', 'test data'))
      .rejects.toThrow('Network error');
  });
});
```

### 2. Integration Testing

```typescript
// test/r2-integration.test.ts
describe('R2 Integration Tests', () => {
  let r2Client: S3Client;
  const testBucket = 'integration-test-bucket';

  beforeAll(() => {
    // Use test environment configuration
    r2Client = loadR2Config('test');
  });

  it('should perform complete CRUD operations', async () => {
    const testKey = `test-${Date.now()}.txt`;
    const testData = 'Integration test data';

    // Upload
    await r2Client.send(new PutObjectCommand({
      Bucket: testBucket,
      Key: testKey,
      Body: testData
    }));

    // Download and verify
    const getResponse = await r2Client.send(new GetObjectCommand({
      Bucket: testBucket,
      Key: testKey
    }));
    const content = await getResponse.Body?.transformToString();
    expect(content).toBe(testData);

    // Delete
    await r2Client.send(new DeleteObjectCommand({
      Bucket: testBucket,
      Key: testKey
    }));

    // Verify deletion
    await expect(r2Client.send(new GetObjectCommand({
      Bucket: testBucket,
      Key: testKey
    }))).rejects.toThrow();
  });
});
```

## ⚡ Performance Optimization

### 1. Connection Pooling

```typescript
// Configure connection pooling
const r2Client = new S3Client({
  region: 'auto',
  endpoint: R2_ENDPOINT,
  credentials: R2_CREDENTIALS,
  forcePathStyle: true,
  maxAttempts: 3,
  requestHandler: {
    connectionTimeout: 5000,
    socketTimeout: 10000
  }
});
```

### 2. Parallel Operations

```typescript
// Upload multiple files in parallel
async function uploadMultipleFiles(bucketName: string, files: Array<{key: string, body: any}>) {
  const uploadPromises = files.map(file =>
    r2Client.send(new PutObjectCommand({
      Bucket: bucketName,
      Key: file.key,
      Body: file.body
    }))
  );

  return await Promise.all(uploadPromises);
}

// Download with concurrency limit
import pLimit from 'p-limit';

const limit = pLimit(5); // Max 5 concurrent downloads

async function downloadMultipleFiles(bucketName: string, keys: string[]) {
  const downloads = keys.map(key =>
    limit(() => r2Client.send(new GetObjectCommand({
      Bucket: bucketName,
      Key: key
    })))
  );

  return await Promise.all(downloads);
}
```

## 🔐 Security Considerations

### 1. Credential Rotation

```typescript
// Implement credential rotation
class RotatingR2Client {
  private client: S3Client;
  private credentialsExpiry: Date;

  constructor() {
    this.refreshCredentials();
  }

  private refreshCredentials() {
    const config = this.loadLatestConfig();
    this.client = new S3Client({
      region: config.region,
      endpoint: config.endpoint,
      credentials: config.credentials,
      forcePathStyle: true
    });
    this.credentialsExpiry = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours
  }

  getClient(): S3Client {
    if (Date.now() > this.credentialsExpiry.getTime()) {
      this.refreshCredentials();
    }
    return this.client;
  }
}
```

### 2. Request Signing Validation

```typescript
import { SignatureV4 } from '@aws-sdk/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-js';

// Validate request signatures
function validateSignature(request: Request, credentials: any): boolean {
  const signer = new SignatureV4({
    credentials,
    region: 'auto',
    service: 's3',
    sha256: Sha256
  });

  // Implementation depends on your specific validation needs
  return true; // Placeholder
}
```

## 📚 Migration from AWS S3

If you're migrating from AWS S3 to R2:

### 1. Code Changes Required

```typescript
// Change endpoint and region
const client = new S3Client({
  region: 'auto', // Changed from AWS region
  endpoint: 'https://account-id.r2.cloudflarestorage.com', // Added
  credentials: {
    accessKeyId: 'R2_ACCESS_KEY', // Different credentials
    secretAccessKey: 'R2_SECRET_KEY'
  },
  forcePathStyle: true // Required for R2
});
```

### 2. Feature Compatibility

**✅ Supported S3 Features:**
- Basic CRUD operations
- Multipart uploads
- Presigned URLs
- Object metadata
- Batch operations

**❌ Unsupported S3 Features:**
- S3 Transfer Acceleration
- S3 Intelligent Tiering
- S3 Glacier storage classes
- Cross-region replication (built into R2)
- S3 Select

### 3. Migration Script Example

```typescript
// migrate-s3-to-r2.ts
async function migrateS3ToR2(s3Client: S3Client, r2Client: S3Client, bucketName: string) {
  let continuationToken: string | undefined;

  do {
    const listResponse = await s3Client.send(new ListObjectsV2Command({
      Bucket: bucketName,
      ContinuationToken: continuationToken
    }));

    if (listResponse.Contents) {
      for (const object of listResponse.Contents) {
        if (!object.Key) continue;

        // Download from S3
        const getResponse = await s3Client.send(new GetObjectCommand({
          Bucket: bucketName,
          Key: object.Key
        }));

        // Upload to R2
        await r2Client.send(new PutObjectCommand({
          Bucket: bucketName,
          Key: object.Key,
          Body: getResponse.Body,
          Metadata: getResponse.Metadata,
          ContentType: getResponse.ContentType
        }));

        console.log(`Migrated: ${object.Key}`);
      }
    }

    continuationToken = listResponse.NextContinuationToken;
  } while (continuationToken);
}
```

## 📚 Additional Resources

- **[AWS SDK v3 Documentation](https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/)**
- **[Cloudflare R2 S3 API Compatibility](https://developers.cloudflare.com/r2/api/s3/)**
- **[S3 API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/)**
- **[Migration Examples](../examples/)** - More migration and integration examples