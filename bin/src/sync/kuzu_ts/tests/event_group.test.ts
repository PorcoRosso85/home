/**
 * EventGroup Transaction Tests (TDD RED Phase)
 * イベントグループのトランザクションテスト（TDD REDフェーズ）
 */

import { assertEquals, assert, assertRejects } from "jsr:@std/assert@^1.0.0";
import type { EventGroup, TemplateEvent } from "../event_sourcing/types.ts";

// EventGroupManager is not yet implemented - this will cause tests to fail
import { EventGroupManager } from "../event_sourcing/event_group_manager.ts";

Deno.test("EventGroup - should create event group with multiple events", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_NODE",
      params: { label: "Person", properties: { name: "Alice" } },
      timestamp: Date.now(),
    },
    {
      id: "event-2",
      template: "CREATE_NODE",
      params: { label: "Person", properties: { name: "Bob" } },
      timestamp: Date.now(),
    },
    {
      id: "event-3",
      template: "CREATE_EDGE",
      params: { type: "KNOWS", fromId: "event-1", toId: "event-2" },
      timestamp: Date.now(),
    },
  ];

  // Act
  const eventGroup = await manager.createEventGroup(events);

  // Assert
  assertEquals(eventGroup.events.length, 3);
  assertEquals(eventGroup.status, "pending");
  assert(eventGroup.id, "EventGroup should have an id");
  assert(eventGroup.timestamp > 0, "EventGroup should have a timestamp");
});

Deno.test("EventGroup - should commit all events atomically", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const testEventStore = {
    committedEvents: [] as TemplateEvent[],
    addEvent: async function(event: TemplateEvent): Promise<void> {
      this.committedEvents.push(event);
    },
  };
  
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_NODE",
      params: { label: "Department", properties: { name: "Engineering" } },
      timestamp: Date.now(),
    },
    {
      id: "event-2",
      template: "CREATE_NODE",
      params: { label: "Employee", properties: { name: "Charlie" } },
      timestamp: Date.now(),
    },
  ];

  // Act
  const eventGroup = await manager.createEventGroup(events);
  await manager.commit(eventGroup.id, testEventStore);

  // Assert
  assertEquals(eventGroup.status, "committed");
  assertEquals(testEventStore.committedEvents.length, 2);
  assertEquals(testEventStore.committedEvents[0].id, "event-1");
  assertEquals(testEventStore.committedEvents[1].id, "event-2");
});

Deno.test("EventGroup - should rollback all events on failure", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const testEventStore = {
    committedEvents: [] as TemplateEvent[],
    addEvent: async function(event: TemplateEvent): Promise<void> {
      // Simulate failure on second event
      if (event.id === "event-2") {
        throw new Error("Storage failure");
      }
      this.committedEvents.push(event);
    },
  };
  
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_NODE",
      params: { label: "Project", properties: { name: "Alpha" } },
      timestamp: Date.now(),
    },
    {
      id: "event-2",
      template: "CREATE_NODE",
      params: { label: "Project", properties: { name: "Beta" } },
      timestamp: Date.now(),
    },
  ];

  // Act
  const eventGroup = await manager.createEventGroup(events);
  
  // Assert
  await assertRejects(
    async () => await manager.commit(eventGroup.id, testEventStore),
    Error,
    "Storage failure"
  );
  
  assertEquals(eventGroup.status, "rolled_back");
  assertEquals(testEventStore.committedEvents.length, 0, "No events should be committed after rollback");
});

Deno.test("EventGroup - should validate all events before committing", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_NODE",
      params: { label: "Person", properties: { name: "David" } },
      timestamp: Date.now(),
    },
    {
      id: "event-2",
      template: "INVALID_TEMPLATE", // Invalid template
      params: { some: "data" },
      timestamp: Date.now(),
    },
  ];

  // Act & Assert
  await assertRejects(
    async () => await manager.createEventGroup(events),
    Error,
    "Invalid template: INVALID_TEMPLATE"
  );
});

Deno.test("EventGroup - should handle empty event list", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const events: TemplateEvent[] = [];

  // Act & Assert
  await assertRejects(
    async () => await manager.createEventGroup(events),
    Error,
    "EventGroup must contain at least one event"
  );
});

Deno.test("EventGroup - should prevent double commit", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const testEventStore = {
    committedEvents: [] as TemplateEvent[],
    addEvent: async function(event: TemplateEvent): Promise<void> {
      this.committedEvents.push(event);
    },
  };
  
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_NODE",
      params: { label: "Task", properties: { title: "Implement feature" } },
      timestamp: Date.now(),
    },
  ];

  // Act
  const eventGroup = await manager.createEventGroup(events);
  await manager.commit(eventGroup.id, testEventStore);

  // Assert - Second commit should fail
  await assertRejects(
    async () => await manager.commit(eventGroup.id, testEventStore),
    Error,
    "EventGroup already committed"
  );
});

Deno.test("EventGroup - should track rollback reason", async () => {
  // Arrange
  const manager = new EventGroupManager();
  const testEventStore = {
    addEvent: async function(event: TemplateEvent): Promise<void> {
      throw new Error("Database connection lost");
    },
  };
  
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "UPDATE_NODE",
      params: { nodeId: "123", properties: { status: "active" } },
      timestamp: Date.now(),
    },
  ];

  // Act
  const eventGroup = await manager.createEventGroup(events);
  try {
    await manager.commit(eventGroup.id, testEventStore);
  } catch (error) {
    // Expected to fail
  }

  // Assert
  const rollbackInfo = await manager.getRollbackInfo(eventGroup.id);
  assertEquals(rollbackInfo.reason, "Database connection lost");
  assert(rollbackInfo.timestamp > 0);
});