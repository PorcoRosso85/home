/**
 * GDPR Logical Delete Event Tests
 * GDPR準拠の論理削除イベントのテスト
 */

import { assertEquals, assertExists, assertRejects } from "jsr:@std/assert@^1.0.0";
import { TemplateEventFactory, TemplateRegistry, TemplateEventStore } from "../event_sourcing/template_event_store.ts";
import { LogicalDeleteHandler, LogicalDeleteEvent } from "../event_sourcing/delete_templates.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

Deno.test("DELETE_USER_DATA template should be registered", () => {
  const registry = new TemplateRegistry();
  const metadata = registry.getTemplateMetadata("DELETE_USER_DATA");
  
  assertExists(metadata);
  assertEquals(metadata.requiredParams, ["userId", "reason"]);
  assertEquals(metadata.impact, "LOGICAL_DELETE");
});

Deno.test("DELETE_USER_DATA event should be created with required parameters", () => {
  const factory = new TemplateEventFactory();
  
  const event = factory.createTemplateEvent("DELETE_USER_DATA", {
    userId: "user123",
    reason: "User requested data deletion under GDPR Article 17"
  });
  
  assertExists(event);
  assertEquals(event.template, "DELETE_USER_DATA");
  assertEquals(event.params.userId, "user123");
  assertEquals(event.params.reason, "User requested data deletion under GDPR Article 17");
  assertExists(event.timestamp);
  assertExists(event.checksum);
});

Deno.test("DELETE_USER_DATA event should fail without required parameters", async () => {
  const factory = new TemplateEventFactory();
  
  // Missing userId
  await assertRejects(
    async () => factory.createTemplateEvent("DELETE_USER_DATA", { reason: "GDPR request" }),
    Error,
    "Missing required parameter: userId"
  );
  
  // Missing reason
  await assertRejects(
    async () => factory.createTemplateEvent("DELETE_USER_DATA", { userId: "user123" }),
    Error,
    "Missing required parameter: reason"
  );
});

Deno.test("LogicalDeleteHandler should mark user data as deleted without physical removal", () => {
  const handler = new LogicalDeleteHandler();
  const store = new TemplateEventStore();
  
  // Create some user data first
  const createUserEvent: TemplateEvent = {
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "user123", name: "John Doe", email: "john@example.com" },
    timestamp: Date.now() - 1000
  };
  store.appendTemplateEvent(createUserEvent);
  
  // Create deletion event
  const deleteEvent: LogicalDeleteEvent = {
    id: "evt_2",
    template: "DELETE_USER_DATA",
    params: { userId: "user123", reason: "GDPR Article 17 request" },
    timestamp: Date.now(),
    deletionTimestamp: Date.now()
  };
  
  // Process deletion
  const result = handler.processLogicalDelete(deleteEvent, store);
  
  // Verify deletion marker is added
  assertEquals(result.isDeleted, true);
  assertEquals(result.deletionReason, "GDPR Article 17 request");
  assertExists(result.deletionTimestamp);
  
  // Verify original events still exist in store
  assertEquals(store.getEventCount(), 2); // Original + deletion event
});

Deno.test("Queries should exclude logically deleted data", () => {
  const handler = new LogicalDeleteHandler();
  const store = new TemplateEventStore();
  
  // Create multiple users
  store.appendTemplateEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "user1", name: "User One" },
    timestamp: Date.now() - 2000
  });
  
  store.appendTemplateEvent({
    id: "evt_2",
    template: "CREATE_USER",
    params: { id: "user2", name: "User Two" },
    timestamp: Date.now() - 1000
  });
  
  // Delete user1
  const deleteEvent: LogicalDeleteEvent = {
    id: "evt_3",
    template: "DELETE_USER_DATA",
    params: { userId: "user1", reason: "User request" },
    timestamp: Date.now(),
    deletionTimestamp: Date.now()
  };
  handler.processLogicalDelete(deleteEvent, store);
  
  // Query active users
  const activeUsers = handler.getActiveEntities(store, "USER");
  
  // Should only return user2
  assertEquals(activeUsers.length, 1);
  assertEquals(activeUsers[0].id, "user2");
});

Deno.test("Deletion reason and timestamp should be tracked", () => {
  const handler = new LogicalDeleteHandler();
  const deleteTime = Date.now();
  
  const deleteEvent: LogicalDeleteEvent = {
    id: "evt_1",
    template: "DELETE_USER_DATA",
    params: { 
      userId: "user123", 
      reason: "Right to be forgotten - Article 17(1)(a)" 
    },
    timestamp: deleteTime,
    deletionTimestamp: deleteTime
  };
  
  const deletionInfo = handler.getDeletionInfo(deleteEvent);
  
  assertEquals(deletionInfo.userId, "user123");
  assertEquals(deletionInfo.reason, "Right to be forgotten - Article 17(1)(a)");
  assertEquals(deletionInfo.deletionTimestamp, deleteTime);
  assertEquals(deletionInfo.isLogicalDelete, true);
});

Deno.test("Multiple deletion events for same user should be handled correctly", () => {
  const handler = new LogicalDeleteHandler();
  const store = new TemplateEventStore();
  
  // First deletion
  const firstDelete: LogicalDeleteEvent = {
    id: "evt_1",
    template: "DELETE_USER_DATA",
    params: { userId: "user123", reason: "Initial request" },
    timestamp: Date.now() - 1000,
    deletionTimestamp: Date.now() - 1000
  };
  handler.processLogicalDelete(firstDelete, store);
  
  // Second deletion (should be ignored or logged as duplicate)
  const secondDelete: LogicalDeleteEvent = {
    id: "evt_2",
    template: "DELETE_USER_DATA",
    params: { userId: "user123", reason: "Duplicate request" },
    timestamp: Date.now(),
    deletionTimestamp: Date.now()
  };
  
  const result = handler.processLogicalDelete(secondDelete, store);
  
  // Should indicate this is a duplicate deletion
  assertEquals(result.isDuplicate, true);
  assertEquals(result.previousDeletionTimestamp, firstDelete.deletionTimestamp);
});

Deno.test("Logical delete should support cascading deletes for related data", () => {
  const handler = new LogicalDeleteHandler();
  const store = new TemplateEventStore();
  
  // Create user and related data
  store.appendTemplateEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "user123", name: "John Doe" },
    timestamp: Date.now() - 3000
  });
  
  store.appendTemplateEvent({
    id: "evt_2",
    template: "CREATE_POST",
    params: { id: "post1", userId: "user123", content: "Hello world" },
    timestamp: Date.now() - 2000
  });
  
  store.appendTemplateEvent({
    id: "evt_3",
    template: "CREATE_POST",
    params: { id: "post2", userId: "user123", content: "Another post" },
    timestamp: Date.now() - 1000
  });
  
  // Delete user (should cascade to posts)
  const deleteEvent: LogicalDeleteEvent = {
    id: "evt_4",
    template: "DELETE_USER_DATA",
    params: { userId: "user123", reason: "GDPR request", cascade: true },
    timestamp: Date.now(),
    deletionTimestamp: Date.now()
  };
  
  const result = handler.processLogicalDelete(deleteEvent, store);
  
  // Verify cascade effect
  assertEquals(result.cascadedEntities.length, 2); // 2 posts
  assertEquals(result.cascadedEntities[0].type, "POST");
  assertEquals(result.cascadedEntities[0].id, "post1");
  assertEquals(result.cascadedEntities[1].id, "post2");
});