import { assertEquals, assertExists, assertStringIncludes } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach, afterEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";

// Import test modules
import { EmailParser } from "./email_parser_test.ts";
import { InMemoryS3Adapter } from "./adapters/in_memory_s3.ts";
import { MetadataExtractor } from "./metadata_extractor_test.ts";
import { EmailArchiveIntegration } from "./integration_test.ts";

// Test configuration
const TEST_CONFIG = {
  bucketName: "test-email-archive",
  region: "us-east-1",
};

describe("Email Archive System", () => {
  let s3Adapter: InMemoryS3Adapter;

  beforeEach(() => {
    s3Adapter = new InMemoryS3Adapter();
  });

  afterEach(() => {
    s3Adapter.clear();
  });

  describe("Email Parser", () => {
    const emailParser = new EmailParser();

    it("should parse simple text email", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/simple_text.eml");
      const parsed = emailParser.parse(rawEmail);
      
      assertEquals(parsed.from, "sender@example.com");
      assertEquals(parsed.to, ["recipient@example.com"]);
      assertEquals(parsed.subject, "Simple Text Email");
      assertExists(parsed.messageId);
      assertStringIncludes(parsed.body, "This is a simple text email");
    });

    it("should parse HTML email with attachments", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/html_with_attachment.eml");
      const parsed = emailParser.parse(rawEmail);
      
      assertEquals(parsed.from, "sender@example.com");
      assertEquals(parsed.to, ["recipient@example.com"]);
      assertEquals(parsed.subject, "HTML Email with Attachment");
      assertEquals(parsed.attachments.length, 1);
      assertEquals(parsed.attachments[0].filename, "document.pdf");
      assertEquals(parsed.attachments[0].contentType, "application/pdf");
    });

    it("should handle multipart email", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/multipart.eml");
      const parsed = emailParser.parse(rawEmail);
      
      assertExists(parsed.textBody);
      assertExists(parsed.htmlBody);
      assertEquals(parsed.from, "sender@example.com");
    });

    it("should handle malformed email gracefully", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/malformed.eml");
      const parsed = emailParser.parse(rawEmail);
      
      // Should not throw and should provide default values
      assertExists(parsed.messageId);
      assertExists(parsed.receivedAt);
    });
  });

  describe("S3 Storage", () => {
    it("should store email with correct key structure", async () => {
      const testData = "test email content";
      const messageId = "test-message-123";
      const date = new Date("2024-01-15T10:30:00Z");
      
      const key = `emails/${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}/${messageId}.eml`;
      
      await s3Adapter.putObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: key,
        Body: testData,
        ContentType: "message/rfc822",
      });

      const result = await s3Adapter.getObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: key,
      });

      assertEquals(result.Body, testData);
      assertEquals(result.ContentType, "message/rfc822");
    });

    it("should store metadata as JSON", async () => {
      const metadata = {
        messageId: "test-message-123",
        from: "sender@example.com",
        to: ["recipient@example.com"],
        subject: "Test Email",
        receivedAt: "2024-01-15T10:30:00Z",
        size: 1234,
      };

      const key = "emails/2024/01/15/test-message-123.json";
      
      await s3Adapter.putObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: key,
        Body: JSON.stringify(metadata),
        ContentType: "application/json",
      });

      const result = await s3Adapter.getObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: key,
      });

      const retrievedMetadata = JSON.parse(result.Body as string);
      assertEquals(retrievedMetadata.messageId, metadata.messageId);
      assertEquals(retrievedMetadata.from, metadata.from);
    });

    it("should handle concurrent storage operations", async () => {
      const operations = [];
      
      for (let i = 0; i < 10; i++) {
        operations.push(
          s3Adapter.putObject({
            Bucket: TEST_CONFIG.bucketName,
            Key: `test-${i}.txt`,
            Body: `content-${i}`,
            ContentType: "text/plain",
          })
        );
      }

      await Promise.all(operations);

      // Verify all objects were stored
      for (let i = 0; i < 10; i++) {
        const result = await s3Adapter.getObject({
          Bucket: TEST_CONFIG.bucketName,
          Key: `test-${i}.txt`,
        });
        assertEquals(result.Body, `content-${i}`);
      }
    });
  });

  describe("Metadata Extraction", () => {
    const metadataExtractor = new MetadataExtractor();

    it("should extract basic metadata", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/simple_text.eml");
      const metadata = metadataExtractor.extract(rawEmail);
      
      assertEquals(metadata.from, "sender@example.com");
      assertEquals(metadata.to, ["recipient@example.com"]);
      assertEquals(metadata.subject, "Simple Text Email");
      assertExists(metadata.messageId);
      assertExists(metadata.receivedAt);
      assertEquals(typeof metadata.size, "number");
    });

    it("should extract attachment metadata", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/html_with_attachment.eml");
      const metadata = metadataExtractor.extract(rawEmail);
      
      assertEquals(metadata.attachments.length, 1);
      assertEquals(metadata.attachments[0].filename, "document.pdf");
      assertEquals(metadata.attachments[0].contentType, "application/pdf");
      assertEquals(typeof metadata.attachments[0].size, "number");
    });

    it("should handle multiple recipients", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/multiple_recipients.eml");
      const metadata = metadataExtractor.extract(rawEmail);
      
      assertEquals(metadata.to.length, 3);
      assertEquals(metadata.to, ["recipient1@example.com", "recipient2@example.com", "recipient3@example.com"]);
    });

    it("should extract custom headers", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/custom_headers.eml");
      const metadata = metadataExtractor.extract(rawEmail);
      
      assertExists(metadata.headers);
      assertEquals(metadata.headers["X-Custom-Header"], "custom-value");
      assertEquals(metadata.headers["X-Priority"], "high");
    });
  });

  describe("Integration Tests", () => {
    const integration = new EmailArchiveIntegration(s3Adapter);

    it("should archive complete email workflow", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/simple_text.eml");
      const messageId = "integration-test-123";
      
      const result = await integration.archiveEmail(rawEmail, {
        bucketName: TEST_CONFIG.bucketName,
        messageId,
        receivedAt: new Date("2024-01-15T10:30:00Z"),
      });

      assertEquals(result.success, true);
      assertEquals(result.messageId, messageId);
      assertExists(result.emlKey);
      assertExists(result.metadataKey);

      // Verify both files were stored
      const emlObject = await s3Adapter.getObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: result.emlKey,
      });
      
      const metadataObject = await s3Adapter.getObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: result.metadataKey,
      });

      assertEquals(emlObject.Body, rawEmail);
      assertEquals(emlObject.ContentType, "message/rfc822");
      
      const metadata = JSON.parse(metadataObject.Body as string);
      assertEquals(metadata.messageId, messageId);
    });

    it("should handle archiving errors gracefully", async () => {
      // Simulate S3 error by using invalid bucket
      const result = await integration.archiveEmail("invalid email", {
        bucketName: "non-existent-bucket",
        messageId: "error-test",
        receivedAt: new Date(),
      });

      assertEquals(result.success, false);
      assertExists(result.error);
    });

    it("should generate unique keys for concurrent requests", async () => {
      const rawEmail = await Deno.readTextFile("./test/fixtures/simple_text.eml");
      const operations = [];

      for (let i = 0; i < 5; i++) {
        operations.push(
          integration.archiveEmail(rawEmail, {
            bucketName: TEST_CONFIG.bucketName,
            messageId: `concurrent-${i}`,
            receivedAt: new Date(),
          })
        );
      }

      const results = await Promise.all(operations);
      
      // All should succeed
      results.forEach(result => assertEquals(result.success, true));
      
      // All should have unique keys
      const keys = results.map(r => r.emlKey);
      const uniqueKeys = new Set(keys);
      assertEquals(uniqueKeys.size, keys.length);
    });

    it("should preserve email integrity", async () => {
      const originalEmail = await Deno.readTextFile("./test/fixtures/html_with_attachment.eml");
      
      const result = await integration.archiveEmail(originalEmail, {
        bucketName: TEST_CONFIG.bucketName,
        messageId: "integrity-test",
        receivedAt: new Date(),
      });

      const retrievedEmail = await s3Adapter.getObject({
        Bucket: TEST_CONFIG.bucketName,
        Key: result.emlKey,
      });

      assertEquals(retrievedEmail.Body, originalEmail);
    });
  });

  describe("Performance Tests", () => {
    it("should handle large emails efficiently", async () => {
      const largeEmail = await Deno.readTextFile("./test/fixtures/large_email.eml");
      const startTime = Date.now();
      
      const integration = new EmailArchiveIntegration(s3Adapter);
      const result = await integration.archiveEmail(largeEmail, {
        bucketName: TEST_CONFIG.bucketName,
        messageId: "large-email-test",
        receivedAt: new Date(),
      });

      const endTime = Date.now();
      const processingTime = endTime - startTime;

      assertEquals(result.success, true);
      console.log(`Large email processing time: ${processingTime}ms`);
      
      // Should process within reasonable time (adjust threshold as needed)
      assertEquals(processingTime < 5000, true, `Processing took too long: ${processingTime}ms`);
    });

    it("should handle batch archiving", async () => {
      const emails = [
        await Deno.readTextFile("./test/fixtures/simple_text.eml"),
        await Deno.readTextFile("./test/fixtures/html_with_attachment.eml"),
        await Deno.readTextFile("./test/fixtures/multipart.eml"),
      ];

      const integration = new EmailArchiveIntegration(s3Adapter);
      const startTime = Date.now();
      
      const operations = emails.map((email, index) =>
        integration.archiveEmail(email, {
          bucketName: TEST_CONFIG.bucketName,
          messageId: `batch-${index}`,
          receivedAt: new Date(),
        })
      );

      const results = await Promise.all(operations);
      const endTime = Date.now();

      results.forEach(result => assertEquals(result.success, true));
      console.log(`Batch processing time: ${endTime - startTime}ms`);
    });
  });
});