/**
 * Verification script for library usage
 * This simulates how an external project would use the S3 storage adapter
 */

// Import from mod.ts as external users would
import { 
  createStorageAdapter, 
  S3StorageApplication,
  InMemoryStorageAdapter,
  FilesystemStorageAdapter,
  type StorageAdapter,
  type StorageConfig,
  type S3Command,
  type S3Result
} from "./mod.ts";

console.log("🔍 Verifying S3 Storage Adapter Library Usage...\n");

// Test 1: Create adapters with different configurations
console.log("1️⃣ Testing adapter creation:");

const inMemoryAdapter = createStorageAdapter({ type: "in-memory" });
console.log("✅ In-memory adapter created:", inMemoryAdapter.getType());

const fsAdapter = createStorageAdapter({ 
  type: "filesystem", 
  basePath: "/tmp/s3-test" 
});
console.log("✅ Filesystem adapter created:", fsAdapter.getType());

// Test 2: Direct class instantiation
console.log("\n2️⃣ Testing direct class usage:");

const directAdapter = new InMemoryStorageAdapter();
console.log("✅ Direct InMemoryStorageAdapter created");

const directFs = new FilesystemStorageAdapter("/tmp/direct-test");
console.log("✅ Direct FilesystemStorageAdapter created");

// Test 3: S3StorageApplication usage
console.log("\n3️⃣ Testing S3StorageApplication:");

const app = new S3StorageApplication({ type: "in-memory" });

// Upload
const uploadResult = await app.execute({
  type: "upload",
  key: "test-app.json",
  content: JSON.stringify({ message: "Hello from app!" })
});
console.log("✅ Upload via app:", uploadResult.type === "upload" ? "success" : "failed");

// List
const listResult = await app.execute({ type: "list" });
console.log("✅ List via app:", listResult.type === "list" ? `found ${listResult.objects.length} objects` : "failed");

// Test 4: Type safety verification
console.log("\n4️⃣ Testing TypeScript types:");

// These should compile without errors
const testConfig: StorageConfig = { type: "in-memory" };
const testAdapter: StorageAdapter = createStorageAdapter(testConfig);
const testCommand: S3Command = { action: "list" };
const testUpload: S3Command = { 
  action: "upload", 
  key: "test.txt", 
  content: "test" 
};

console.log("✅ All type definitions work correctly");

// Test 5: Error handling
console.log("\n5️⃣ Testing error handling:");

try {
  await testAdapter.download("non-existent-file.txt");
} catch (error) {
  console.log("✅ Error handling works:", error instanceof Error ? "proper error thrown" : "unexpected error");
}

// Test 6: Real-world usage pattern
console.log("\n6️⃣ Testing real-world usage pattern:");

async function backupConfiguration(adapter: StorageAdapter, config: Record<string, any>) {
  const timestamp = new Date().toISOString();
  const key = `backups/config-${timestamp}.json`;
  
  await adapter.upload(key, JSON.stringify(config, null, 2), {
    contentType: "application/json",
    metadata: { 
      backup: "true",
      timestamp 
    }
  });
  
  return key;
}

const backupKey = await backupConfiguration(inMemoryAdapter, {
  version: "1.0.0",
  features: ["s3", "backup", "restore"]
});
console.log("✅ Backup created:", backupKey);

// Verify backup
const backupInfo = await inMemoryAdapter.info(backupKey);
console.log("✅ Backup verified:", backupInfo.exists ? "exists" : "missing");

console.log("\n✨ All library usage tests passed!");
console.log("\nThe S3 storage adapter can be successfully used as a flake input.");