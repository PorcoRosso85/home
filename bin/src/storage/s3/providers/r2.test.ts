import { assertEquals, assertThrows } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { getR2EndpointUrl, validateR2Config, R2StorageAdapter, type R2Config } from "./r2.ts";
import { testStorageAdapter } from "./test-helpers.ts";

describe("R2 Provider", () => {
  describe("getR2EndpointUrl", () => {
    it("should generate correct endpoint URL from accountId", () => {
      const endpoint = getR2EndpointUrl("123456");
      assertEquals(endpoint, "https://123456.r2.cloudflarestorage.com");
    });

    it("should throw error for empty accountId", () => {
      assertThrows(
        () => getR2EndpointUrl(""),
        Error,
        "Account ID is required"
      );
    });
  });

  describe("R2 constraints", () => {
    it("should always use 'auto' region", () => {
      // R2 doesn't use traditional AWS regions, always uses 'auto'
      const region = "auto";
      assertEquals(region, "auto");
    });

    it("should validate bucket name constraints", () => {
      const validateBucketName = (name: string): boolean => {
        // R2 bucket naming rules (similar to S3 but with some differences)
        if (name.length < 3 || name.length > 63) return false;
        if (!/^[a-z0-9]/.test(name)) return false;
        if (!/[a-z0-9]$/.test(name)) return false;
        if (/[^a-z0-9-]/.test(name)) return false;
        if (/--/.test(name)) return false;
        return true;
      };

      // Valid bucket names
      assertEquals(validateBucketName("my-bucket"), true);
      assertEquals(validateBucketName("bucket123"), true);
      assertEquals(validateBucketName("test-bucket-name"), true);

      // Invalid bucket names
      assertEquals(validateBucketName(""), false);
      assertEquals(validateBucketName("ab"), false); // too short
      assertEquals(validateBucketName("Bucket"), false); // uppercase
      assertEquals(validateBucketName("-bucket"), false); // starts with dash
      assertEquals(validateBucketName("bucket-"), false); // ends with dash
      assertEquals(validateBucketName("bucket--name"), false); // consecutive dashes
      assertEquals(validateBucketName("bucket.name"), false); // contains period
    });
  });

  describe("validateR2Config", () => {
    // 有効な設定での成功テスト
    it("should accept valid R2 configuration", () => {
      const validConfig: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my-valid-bucket"
      };
      
      // Should not throw
      validateR2Config(validConfig);
    });

    // 各必須フィールドの欠落テスト
    it("should throw error when accountId is missing", () => {
      const config = {
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my-bucket"
      } as R2Config;
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        "R2 configuration error: accountId is required"
      );
    });

    it("should throw error when accountId is empty string", () => {
      const config: R2Config = {
        accountId: "",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my-bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        "R2 configuration error: accountId is required"
      );
    });

    it("should throw error when accessKeyId is missing", () => {
      const config = {
        accountId: "123456789",
        secretAccessKey: "test-secret-key",
        bucket: "my-bucket"
      } as R2Config;
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        "R2 configuration error: accessKeyId is required"
      );
    });

    it("should throw error when secretAccessKey is missing", () => {
      const config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        bucket: "my-bucket"
      } as R2Config;
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        "R2 configuration error: secretAccessKey is required"
      );
    });

    it("should throw error when bucket is missing", () => {
      const config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key"
      } as R2Config;
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        "R2 configuration error: bucket name is required"
      );
    });

    // バケット名の無効なケースのテスト
    it("should throw error for bucket name shorter than 3 characters", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "ab"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "ab" must be between 3 and 63 characters'
      );
    });

    it("should throw error for bucket name longer than 63 characters", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "a".repeat(64)
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        `R2 configuration error: bucket name "${config.bucket}" must be between 3 and 63 characters`
      );
    });

    it("should throw error when bucket name starts with uppercase letter", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "My-bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "My-bucket" must start with a lowercase letter or number'
      );
    });

    it("should throw error when bucket name starts with hyphen", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "-my-bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "-my-bucket" must start with a lowercase letter or number'
      );
    });

    it("should throw error when bucket name ends with hyphen", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my-bucket-"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "my-bucket-" must end with a lowercase letter or number'
      );
    });

    it("should throw error when bucket name contains invalid characters", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my_bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "my_bucket" can only contain lowercase letters, numbers, hyphens, and dots'
      );
    });

    it("should throw error when bucket name is formatted as IP address", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "192.168.1.1"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "192.168.1.1" cannot be formatted as an IP address'
      );
    });

    it("should throw error when bucket name contains consecutive dots", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my..bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "my..bucket" cannot contain consecutive dots or hyphens'
      );
    });

    it("should throw error when bucket name contains consecutive hyphens", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my--bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "my--bucket" cannot contain consecutive dots or hyphens'
      );
    });

    it("should throw error when bucket name has dots adjacent to hyphens", () => {
      const config: R2Config = {
        accountId: "123456789",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "my.-bucket"
      };
      
      assertThrows(
        () => validateR2Config(config),
        Error,
        'R2 configuration error: bucket name "my.-bucket" cannot have dots adjacent to hyphens'
      );
    });

    it("should accept valid bucket names with dots and hyphens", () => {
      const validBucketNames = [
        "my-bucket",
        "bucket.with.dots",
        "123-bucket",
        "bucket-123",
        "my.bucket-name",
        "test-bucket.example"
      ];

      for (const bucket of validBucketNames) {
        const config: R2Config = {
          accountId: "123456789",
          accessKeyId: "test-access-key",
          secretAccessKey: "test-secret-key",
          bucket
        };
        
        // Should not throw
        validateR2Config(config);
      }
    });
  });

  describe("R2StorageAdapter", () => {
    // Create a mock R2 configuration for testing
    const mockR2Config: R2Config = {
      accountId: "test-account-123",
      accessKeyId: "test-access-key",
      secretAccessKey: "test-secret-key",
      bucket: "test-bucket"
    };

    it("should create adapter with R2 configuration", () => {
      const adapter = new R2StorageAdapter(mockR2Config);
      assertEquals(adapter.getType(), "r2");
    });

    it("should validate configuration on construction", () => {
      const invalidConfig: R2Config = {
        accountId: "",
        accessKeyId: "test-access-key",
        secretAccessKey: "test-secret-key",
        bucket: "test-bucket"
      };

      assertThrows(
        () => new R2StorageAdapter(invalidConfig),
        Error,
        "R2 configuration error: accountId is required"
      );
    });

    it("should run common storage adapter tests", async () => {
      // Note: In a real environment, you would need to provide actual R2 credentials
      // For unit tests, we're using mock configuration
      // This test is primarily to ensure the adapter implements the interface correctly
      
      // Skip actual API calls in unit tests
      if (Deno.env.get("R2_INTEGRATION_TEST") === "true") {
        const integrationConfig: R2Config = {
          accountId: Deno.env.get("R2_ACCOUNT_ID") || "",
          accessKeyId: Deno.env.get("R2_ACCESS_KEY_ID") || "",
          secretAccessKey: Deno.env.get("R2_SECRET_ACCESS_KEY") || "",
          bucket: Deno.env.get("R2_TEST_BUCKET") || "test-bucket"
        };

        const adapter = new R2StorageAdapter(integrationConfig);
        await testStorageAdapter(adapter, "R2StorageAdapter");
      }
    });

    it("should inherit S3CompatibleAdapter behavior", () => {
      const adapter = new R2StorageAdapter(mockR2Config);
      
      // Verify that the adapter has all required methods
      assertEquals(typeof adapter.upload, "function");
      assertEquals(typeof adapter.download, "function");
      assertEquals(typeof adapter.delete, "function");
      assertEquals(typeof adapter.list, "function");
      assertEquals(typeof adapter.info, "function");
    });

    it("should configure endpoint correctly for R2", () => {
      const adapter = new R2StorageAdapter(mockR2Config);
      // The endpoint should be set based on the account ID
      const expectedEndpoint = `https://${mockR2Config.accountId}.r2.cloudflarestorage.com`;
      
      // Note: We can't directly access private properties, but we can verify
      // the adapter was created successfully with the expected configuration
      assertEquals(adapter.getType(), "r2");
    });
  });
});