import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

/**
 * Email Archive Worker
 * Archives incoming emails to MinIO S3-compatible storage
 */
export default {
  async fetch(request, env, ctx) {
    // For development mode, handle HTTP requests
    if (env.DEV_MODE === "true") {
      const url = new URL(request.url);
      
      // Simple health check endpoint
      if (url.pathname === "/__health") {
        return new Response(JSON.stringify({
          status: 'ok',
          timestamp: new Date().toISOString(),
          mode: 'production-with-dev-endpoints',
          environment: {
            MINIO_ENDPOINT: env.MINIO_ENDPOINT,
            BUCKET_NAME: env.BUCKET_NAME
          }
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // Default response for HTTP requests in production
    return new Response('Email Archive Worker - Use email routing for processing emails.', {
      status: 200,
      headers: { 'Content-Type': 'text/plain' }
    });
  },

  async email(message, env, ctx) {
    const startTime = Date.now();
    
    try {
      console.log(`[${new Date().toISOString()}] Processing email from: ${message.from}`);
      
      // Initialize S3 client for MinIO
      const s3Client = new S3Client({
        endpoint: env.MINIO_ENDPOINT || "http://localhost:9000",
        region: "us-east-1", // MinIO requires a region
        credentials: {
          accessKeyId: env.MINIO_ACCESS_KEY || "minioadmin",
          secretAccessKey: env.MINIO_SECRET_KEY || "minioadmin",
        },
        forcePathStyle: true, // Required for MinIO compatibility
      });

      // Get raw email content
      const rawEmail = await message.raw();
      console.log(`Raw email size: ${rawEmail.length} bytes`);

      // Extract comprehensive metadata
      const metadata = await extractEmailMetadata(message, rawEmail);
      console.log(`Extracted metadata for message: ${metadata.messageId}`);

      // Generate storage paths
      const storageKey = generateStorageKey(metadata);
      console.log(`Storage key: ${storageKey}`);

      // Archive email and metadata to S3
      await archiveToS3(s3Client, env.BUCKET_NAME || "email-archive", storageKey, rawEmail, metadata);

      const processingTime = Date.now() - startTime;
      console.log(`[${new Date().toISOString()}] Email archived successfully in ${processingTime}ms: ${storageKey}`);
      
      return new Response(`Email archived successfully: ${metadata.messageId}`, {
        status: 200,
        headers: { "Content-Type": "text/plain" }
      });

    } catch (error) {
      const processingTime = Date.now() - startTime;
      console.error(`[${new Date().toISOString()}] Archive error after ${processingTime}ms:`, {
        error: error.message,
        stack: error.stack,
        from: message.from,
        to: message.to
      });

      // Don't throw - this would cause the email to be rejected
      // Instead, log error and return success to prevent email bounce
      return new Response(`Archive failed: ${error.message}`, {
        status: 500,
        headers: { "Content-Type": "text/plain" }
      });
    }
  }
};

/**
 * Extract comprehensive metadata from email message
 */
async function extractEmailMetadata(message, rawEmail) {
  const headers = {};
  
  // Extract all headers
  for (const [key, value] of message.headers.entries()) {
    headers[key] = value;
  }

  // Generate message ID if not present
  let messageId = headers["message-id"];
  if (!messageId) {
    messageId = `generated-${Date.now()}-${Math.random().toString(36).substr(2, 9)}@worker.local`;
    console.warn("No message-id found, generated:", messageId);
  }

  // Clean message ID for filename safety
  const cleanMessageId = messageId.replace(/[<>]/g, '').replace(/[^a-zA-Z0-9@._-]/g, '_');

  // Extract recipients
  const recipients = Array.isArray(message.to) ? message.to : [message.to].filter(Boolean);

  // Parse date
  const receivedAt = new Date().toISOString();
  const emailDate = headers["date"] ? new Date(headers["date"]).toISOString() : receivedAt;

  // Extract content info
  const contentType = headers["content-type"] || "text/plain";
  const isMultipart = contentType.toLowerCase().includes("multipart");

  // Build comprehensive metadata
  const metadata = {
    messageId: cleanMessageId,
    originalMessageId: messageId,
    receivedAt,
    emailDate,
    from: message.from,
    to: recipients,
    subject: headers["subject"] || "(No Subject)",
    size: rawEmail.length,
    contentType,
    isMultipart,
    headers,
    // Add processing info
    archivedBy: "email-archive-worker",
    workerVersion: "1.0.0"
  };

  // Extract attachment info if multipart
  if (isMultipart) {
    try {
      metadata.attachments = await extractAttachmentInfo(rawEmail);
    } catch (error) {
      console.warn("Failed to extract attachment info:", error.message);
      metadata.attachments = [];
    }
  }

  return metadata;
}

/**
 * Extract attachment information from multipart email
 */
async function extractAttachmentInfo(rawEmail) {
  const attachments = [];
  const emailText = new TextDecoder().decode(rawEmail);
  
  // Simple attachment detection - look for Content-Disposition: attachment
  const attachmentRegex = /Content-Disposition:\s*attachment[;\s]*filename[=\s]*["']?([^"'\r\n]+)["']?/gi;
  let match;
  
  while ((match = attachmentRegex.exec(emailText)) !== null) {
    attachments.push({
      filename: match[1],
      contentType: "application/octet-stream", // Default, could be enhanced
      detectedAt: new Date().toISOString()
    });
  }
  
  return attachments;
}

/**
 * Generate hierarchical storage key based on date and message ID
 */
function generateStorageKey(metadata) {
  const date = new Date(metadata.receivedAt);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  return `emails/${year}/${month}/${day}/${metadata.messageId}`;
}

/**
 * Archive email and metadata to S3 storage
 */
async function archiveToS3(s3Client, bucketName, storageKey, rawEmail, metadata) {
  const operations = [];

  // Store raw email (.eml file)
  operations.push(
    s3Client.send(new PutObjectCommand({
      Bucket: bucketName,
      Key: `${storageKey}.eml`,
      Body: rawEmail,
      ContentType: "message/rfc822",
      Metadata: {
        "archived-at": new Date().toISOString(),
        "message-id": metadata.messageId,
        "from": metadata.from,
        "subject": metadata.subject.substring(0, 100) // Truncate for metadata limits
      }
    }))
  );

  // Store metadata (.json file)
  operations.push(
    s3Client.send(new PutObjectCommand({
      Bucket: bucketName,
      Key: `${storageKey}.json`,
      Body: JSON.stringify(metadata, null, 2),
      ContentType: "application/json",
      Metadata: {
        "archived-at": new Date().toISOString(),
        "message-id": metadata.messageId,
        "metadata-version": "1.0"
      }
    }))
  );

  // Execute both operations in parallel
  await Promise.all(operations);
  
  console.log(`Stored both .eml and .json files for: ${storageKey}`);
}