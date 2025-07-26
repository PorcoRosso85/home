/**
 * Archive Executor Test Suite - TDD RED Phase
 * Tests for transactional archiving with rollback capabilities
 */

import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { InMemoryStorageAdapter } from "../../../storage/s3/providers/in-memory.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

// Import the implemented ArchiveExecutor
import { ArchiveExecutor, type ArchiveOperation, type ArchiveResult } from "../event_sourcing/archive_executor.ts";

describe("ArchiveExecutor", () => {
  const createTestEvent = (id: string, timestamp?: number): TemplateEvent => ({
    id,
    template: "test_template",
    params: { value: `test-${id}` },
    timestamp: timestamp || Date.now(),
    clientId: "test-client"
  });

  const createLocalFile = async (path: string, content: string): Promise<void> => {
    await Deno.writeTextFile(path, content);
  };

  const fileExists = async (path: string): Promise<boolean> => {
    try {
      await Deno.stat(path);
      return true;
    } catch {
      return false;
    }
  };

  describe("execute method", () => {
    it("should upload events to S3 and delete local files on success", async () => {
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage, {
        verifyAfterUpload: true,
        deleteLocalAfterVerify: true
      });

      const event1 = createTestEvent("event-1");
      const event2 = createTestEvent("event-2");
      
      const operations: ArchiveOperation[] = [
        { event: event1, localPath: "/tmp/event-1.json" },
        { event: event2, localPath: "/tmp/event-2.json" }
      ];

      // Create local files
      await createLocalFile(operations[0].localPath, JSON.stringify(event1));
      await createLocalFile(operations[1].localPath, JSON.stringify(event2));

      // Execute archive operations
      const result = await executor.execute(operations);

      // Verify all operations succeeded
      assertEquals(result.successful.length, 2);
      assertEquals(result.failed.length, 0);

      // Verify events are in S3
      const list = await storage.list({ prefix: "events/" });
      assertEquals(list.objects.length, 2);

      // Verify local files are deleted
      assertEquals(await fileExists(operations[0].localPath), false);
      assertEquals(await fileExists(operations[1].localPath), false);
    });

    it("should handle partial batch failures gracefully", async () => {
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage);

      const event1 = createTestEvent("event-1");
      const event2 = createTestEvent("event-2");
      const event3 = createTestEvent("event-3");
      
      const operations: ArchiveOperation[] = [
        { event: event1, localPath: "/tmp/event-1.json" },
        { event: event2, localPath: "/tmp/invalid/path/event-2.json" }, // This will fail
        { event: event3, localPath: "/tmp/event-3.json" }
      ];

      // Create only valid local files
      await createLocalFile(operations[0].localPath, JSON.stringify(event1));
      await createLocalFile(operations[2].localPath, JSON.stringify(event3));

      // Execute archive operations
      const result = await executor.execute(operations);

      // Verify partial success
      assertEquals(result.successful.length, 2);
      assertEquals(result.failed.length, 1);
      assertEquals(result.failed[0].operation, operations[1]);
    });
  });

  describe("executeTransactional method", () => {
    it("should rollback all operations on S3 upload failure", async () => {
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage);

      const event1 = createTestEvent("event-1");
      const event2 = createTestEvent("event-2");
      
      const operations: ArchiveOperation[] = [
        { event: event1, localPath: "/tmp/event-1.json" },
        { event: event2, localPath: "/tmp/event-2.json" }
      ];

      // Create local files
      await createLocalFile(operations[0].localPath, JSON.stringify(event1));
      await createLocalFile(operations[1].localPath, JSON.stringify(event2));

      // Mock S3 failure by creating an invalid event
      const invalidEvent = { ...event2, id: null } as any; // This should cause validation error
      operations[1].event = invalidEvent;

      // Execute should throw and rollback
      await assertRejects(
        async () => await executor.executeTransactional(operations),
        Error,
        "Transaction failed"
      );

      // Verify no events in S3
      const list = await storage.list({ prefix: "events/" });
      assertEquals(list.objects.length, 0);

      // Verify local files still exist (not deleted)
      assertEquals(await fileExists(operations[0].localPath), true);
      assertEquals(await fileExists(operations[1].localPath), true);
    });

    it("should rollback on verification failure", async () => {
      const storage = new InMemoryStorageAdapter();
      
      // Mock verification failure
      const mockStorage = new Proxy(storage, {
        get(target, prop) {
          if (prop === "download") {
            return async () => {
              throw new Error("Verification failed: object not found");
            };
          }
          return target[prop as keyof InMemoryStorageAdapter];
        }
      }) as InMemoryStorageAdapter;

      const executor = new ArchiveExecutor(mockStorage, {
        verifyAfterUpload: true
      });

      const event = createTestEvent("event-1");
      const operations: ArchiveOperation[] = [
        { event, localPath: "/tmp/event-1.json" }
      ];

      await createLocalFile(operations[0].localPath, JSON.stringify(event));

      // Execute should throw due to verification failure
      await assertRejects(
        async () => await executor.executeTransactional(operations),
        Error,
        "Verification failed"
      );

      // Verify local file still exists
      assertEquals(await fileExists(operations[0].localPath), true);
    });

    it("should maintain data integrity during concurrent operations", async () => {
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage, {
        verifyAfterUpload: true,
        deleteLocalAfterVerify: true
      });

      const operations1: ArchiveOperation[] = [
        { event: createTestEvent("event-1"), localPath: "/tmp/event-1.json" },
        { event: createTestEvent("event-2"), localPath: "/tmp/event-2.json" }
      ];

      const operations2: ArchiveOperation[] = [
        { event: createTestEvent("event-3"), localPath: "/tmp/event-3.json" },
        { event: createTestEvent("event-4"), localPath: "/tmp/event-4.json" }
      ];

      // Create all local files
      for (const op of [...operations1, ...operations2]) {
        await createLocalFile(op.localPath, JSON.stringify(op.event));
      }

      // Execute concurrently
      const [result1, result2] = await Promise.all([
        executor.executeTransactional(operations1),
        executor.executeTransactional(operations2)
      ]);

      // Verify all events are archived
      const list = await storage.list({ prefix: "events/" });
      assertEquals(list.objects.length, 4);

      // Verify all local files are deleted
      for (const op of [...operations1, ...operations2]) {
        assertEquals(await fileExists(op.localPath), false);
      }
    });

    it("should respect batch size limits", async () => {
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage, {
        batchSize: 2
      });

      const operations: ArchiveOperation[] = Array.from({ length: 5 }, (_, i) => ({
        event: createTestEvent(`event-${i}`),
        localPath: `/tmp/event-${i}.json`
      }));

      // Create all local files
      for (const op of operations) {
        await createLocalFile(op.localPath, JSON.stringify(op.event));
      }

      // Track upload batches
      let uploadCount = 0;
      const mockStorage = new Proxy(storage, {
        get(target, prop) {
          if (prop === "upload") {
            return async (key: string, content: string | Uint8Array, options?: any) => {
              uploadCount++;
              return target.upload(key, content, options);
            };
          }
          return target[prop as keyof InMemoryStorageAdapter];
        }
      }) as InMemoryStorageAdapter;

      const batchedExecutor = new ArchiveExecutor(mockStorage, {
        batchSize: 2
      });

      await batchedExecutor.executeTransactional(operations);

      // Should process in 3 batches: 2 + 2 + 1
      assertEquals(uploadCount, 5);
      
      // Verify all events are archived
      const list = await storage.list({ prefix: "events/" });
      assertEquals(list.objects.length, 5);
    });

    it("should handle transaction cleanup on unexpected errors", async () => {
      // Ensure clean state - remove any leftover files
      try {
        await Deno.remove("/tmp/event-1.json");
      } catch {
        // Ignore if doesn't exist
      }
      
      const storage = new InMemoryStorageAdapter();
      const executor = new ArchiveExecutor(storage);

      const event = createTestEvent("event-1");
      const operations: ArchiveOperation[] = [
        { event, localPath: "/tmp/event-1.json" }
      ];

      // Don't create the local file to simulate unexpected error
      // This should cause a file read error

      await assertRejects(
        async () => await executor.executeTransactional(operations),
        Error
      );

      // Verify no partial state in S3
      const list = await storage.list({ prefix: "events/" });
      assertEquals(list.objects.length, 0);
    });
  });

  // Cleanup helper for tests
  const cleanup = async () => {
    const testPaths = [
      "/tmp/event-1.json",
      "/tmp/event-2.json",
      "/tmp/event-3.json",
      "/tmp/event-4.json",
      "/tmp/event-5.json"
    ];

    for (const path of testPaths) {
      try {
        await Deno.remove(path);
      } catch {
        // Ignore errors if file doesn't exist
      }
    }
  };

  // Clean up after all tests complete
  // Note: Do not use global event listeners as they can interfere with test execution
});