/**
 * Template-based Event Sourcing - TDD Red Phase Tests
 * テンプレートベースのイベントソーシング基盤のテスト
 */

import { assertEquals, assertThrows, assert } from "@std/assert";
import { join } from "@std/path";

// ========== 型定義 ==========

interface TemplateMetadata {
  requiredParams: string[];
  paramTypes?: Record<string, string>;
  impact: "CREATE_NODE" | "UPDATE_NODE" | "DELETE_NODE" | "CREATE_EDGE" | "UPDATE_EDGE" | "DELETE_EDGE";
  validation?: Record<string, any>;
}

interface TemplateEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
}

interface TemplateEventStore {
  appendTemplateEvent(event: TemplateEvent): void;
  getEventsSince(position: number): TemplateEvent[];
  getLatestEvents(n: number): TemplateEvent[];
  getEventCount(): number;
}

// ========== 1. テンプレート管理 ==========

Deno.test("loadTemplate_with_valid_file_returns_query_string", async () => {
  const templateLoader = new TemplateLoader();
  const query = await templateLoader.loadTemplate("create_user.cypher");
  
  assert(query.includes("CREATE"));
  assert(query.includes("User"));
  assert(query.includes("$id"));
});

Deno.test("loadTemplate_with_nonexistent_file_throws_error", async () => {
  const templateLoader = new TemplateLoader();
  
  await assertThrows(
    async () => await templateLoader.loadTemplate("nonexistent.cypher"),
    Error,
    "Template not found"
  );
});

Deno.test("getTemplateMetadata_with_valid_template_returns_required_params", () => {
  const registry = new TemplateRegistry();
  const metadata = registry.getTemplateMetadata("CREATE_USER");
  
  assertEquals(metadata.requiredParams, ["id", "name", "email", "createdAt"]);
  assertEquals(metadata.impact, "CREATE_NODE");
});

Deno.test("validateTemplate_with_missing_params_throws_error", () => {
  const validator = new TemplateValidator();
  
  assertThrows(
    () => validator.validateTemplate("CREATE_USER", { id: "u1", name: "Alice" }),
    Error,
    "Missing required parameter: email"
  );
});

// ========== 2. イベント生成 ==========

Deno.test("createTemplateEvent_with_valid_params_returns_event", () => {
  const factory = new TemplateEventFactory();
  const event = factory.createTemplateEvent("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  assertEquals(event.template, "CREATE_USER");
  assertEquals(event.params.name, "Alice");
  assert(event.id);
  assert(event.timestamp);
});

Deno.test("createTemplateEvent_with_invalid_template_throws_error", () => {
  const factory = new TemplateEventFactory();
  
  assertThrows(
    () => factory.createTemplateEvent("INVALID_TEMPLATE", {}),
    Error,
    "Unknown template"
  );
});

Deno.test("createTemplateEvent_adds_timestamp_and_id", () => {
  const factory = new TemplateEventFactory();
  const beforeTime = Date.now();
  
  const event = factory.createTemplateEvent("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  const afterTime = Date.now();
  
  assert(event.timestamp >= beforeTime);
  assert(event.timestamp <= afterTime);
  assert(event.id.startsWith("evt_"));
});

Deno.test("createTemplateEvent_calculates_checksum", () => {
  const factory = new TemplateEventFactory();
  const event = factory.createTemplateEvent("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: "2024-01-01T00:00:00Z"
  });
  
  assert(event.checksum);
  assertEquals(event.checksum.length, 64); // SHA-256 hex length
});

// ========== 3. パラメータ検証 ==========

Deno.test("validateParams_with_all_required_params_passes", () => {
  const validator = new ParamValidator();
  const metadata: TemplateMetadata = {
    requiredParams: ["id", "name"],
    impact: "CREATE_NODE"
  };
  
  // Should not throw
  validator.validateParams({ id: "u1", name: "Alice" }, metadata);
});

Deno.test("validateParams_with_missing_required_param_throws_error", () => {
  const validator = new ParamValidator();
  const metadata: TemplateMetadata = {
    requiredParams: ["id", "name", "email"],
    impact: "CREATE_NODE"
  };
  
  assertThrows(
    () => validator.validateParams({ id: "u1", name: "Alice" }, metadata),
    Error,
    "Missing required parameter: email"
  );
});

Deno.test("validateParams_with_invalid_type_throws_error", () => {
  const validator = new ParamValidator();
  const metadata: TemplateMetadata = {
    requiredParams: ["age"],
    paramTypes: { age: "number" },
    impact: "UPDATE_NODE"
  };
  
  assertThrows(
    () => validator.validateParams({ age: "thirty" }, metadata),
    Error,
    "Invalid type for parameter age"
  );
});

Deno.test("validateParams_sanitizes_dangerous_values", () => {
  const validator = new ParamValidator();
  const metadata: TemplateMetadata = {
    requiredParams: ["name"],
    impact: "CREATE_NODE"
  };
  
  const sanitized = validator.validateParams(
    { name: "Alice'; DROP TABLE users; --" },
    metadata
  );
  
  assert(!sanitized.name.includes("DROP"));
});

// ========== 4. イベントストア基本操作 ==========

Deno.test("appendTemplateEvent_stores_event_in_order", () => {
  const store = new TemplateEventStore();
  
  const event1 = { id: "evt_1", template: "CREATE_USER", params: {}, timestamp: 1 };
  const event2 = { id: "evt_2", template: "UPDATE_USER", params: {}, timestamp: 2 };
  
  store.appendTemplateEvent(event1);
  store.appendTemplateEvent(event2);
  
  const events = store.getEventsSince(0);
  assertEquals(events[0].id, "evt_1");
  assertEquals(events[1].id, "evt_2");
});

Deno.test("appendTemplateEvent_increments_event_count", () => {
  const store = new TemplateEventStore();
  
  assertEquals(store.getEventCount(), 0);
  
  store.appendTemplateEvent({ id: "evt_1", template: "CREATE_USER", params: {}, timestamp: 1 });
  assertEquals(store.getEventCount(), 1);
  
  store.appendTemplateEvent({ id: "evt_2", template: "UPDATE_USER", params: {}, timestamp: 2 });
  assertEquals(store.getEventCount(), 2);
});

Deno.test("getEventsSince_returns_events_after_position", () => {
  const store = new TemplateEventStore();
  
  for (let i = 1; i <= 10; i++) {
    store.appendTemplateEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: {},
      timestamp: i
    });
  }
  
  const events = store.getEventsSince(5);
  assertEquals(events.length, 5);
  assertEquals(events[0].id, "evt_6");
});

Deno.test("getLatestEvents_returns_n_most_recent_events", () => {
  const store = new TemplateEventStore();
  
  for (let i = 1; i <= 100; i++) {
    store.appendTemplateEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: {},
      timestamp: i
    });
  }
  
  const latest = store.getLatestEvents(10);
  assertEquals(latest.length, 10);
  assertEquals(latest[0].id, "evt_91");
  assertEquals(latest[9].id, "evt_100");
});

// ========== 5. スナップショット機能 ==========

Deno.test("createSnapshot_after_n_events_stores_state", () => {
  const store = new SnapshotableEventStore({ snapshotInterval: 5 });
  
  for (let i = 1; i <= 10; i++) {
    store.appendTemplateEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}` },
      timestamp: i
    });
  }
  
  const snapshots = store.getSnapshots();
  assertEquals(snapshots.length, 2);
  assertEquals(snapshots[0].position, 5);
  assertEquals(snapshots[1].position, 10);
});

Deno.test("restoreFromSnapshot_rebuilds_state_correctly", () => {
  const store1 = new SnapshotableEventStore({ snapshotInterval: 3 });
  
  for (let i = 1; i <= 5; i++) {
    store1.appendTemplateEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}` },
      timestamp: i
    });
  }
  
  const snapshot = store1.getSnapshotAt(3);
  
  const store2 = new SnapshotableEventStore();
  store2.restoreFromSnapshot(snapshot);
  
  assertEquals(store2.getEventCount(), 3);
});

Deno.test("getStateWithSnapshot_uses_nearest_snapshot_plus_delta", () => {
  const store = new SnapshotableEventStore({ snapshotInterval: 5 });
  
  for (let i = 1; i <= 8; i++) {
    store.appendTemplateEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}` },
      timestamp: i
    });
  }
  
  const state = store.getStateWithSnapshot();
  assert(state.fromSnapshot);
  assertEquals(state.snapshotPosition, 5);
  assertEquals(state.deltaCount, 3);
});

// ========== 6. テンプレート実行の影響予測 ==========

Deno.test("predictImpact_for_create_user_returns_added_node_count", () => {
  const predictor = new ImpactPredictor();
  const impact = predictor.predictImpact("CREATE_USER", { id: "u1" });
  
  assertEquals(impact.addedNodes, 1);
  assertEquals(impact.addedEdges, 0);
  assertEquals(impact.deletedNodes, 0);
});

Deno.test("predictImpact_for_follow_user_returns_added_edge_count", () => {
  const predictor = new ImpactPredictor();
  const impact = predictor.predictImpact("FOLLOW_USER", {
    followerId: "u1",
    targetId: "u2"
  });
  
  assertEquals(impact.addedNodes, 0);
  assertEquals(impact.addedEdges, 1);
  assertEquals(impact.edgeType, "FOLLOWS");
});

Deno.test("predictImpact_for_delete_posts_estimates_affected_nodes", () => {
  const predictor = new ImpactPredictor();
  const impact = predictor.predictImpact("DELETE_OLD_POSTS", {
    beforeDate: "2023-01-01"
  });
  
  assert(impact.deletedNodes >= 0);
  assert(impact.warning?.includes("estimated"));
});

// ========== 7. 同期とブロードキャスト ==========

Deno.test("broadcastEvent_excludes_sender_client", () => {
  const broadcaster = new EventBroadcaster();
  const clients = ["client1", "client2", "client3"];
  
  const event: TemplateEvent = {
    id: "evt_1",
    template: "CREATE_USER",
    params: {},
    timestamp: Date.now(),
    clientId: "client1"
  };
  
  const recipients = broadcaster.broadcastEvent(event, clients);
  assertEquals(recipients, ["client2", "client3"]);
});

Deno.test("receiveTemplateEvent_validates_before_applying", () => {
  const receiver = new EventReceiver();
  
  const invalidEvent: TemplateEvent = {
    id: "evt_1",
    template: "UNKNOWN_TEMPLATE",
    params: {},
    timestamp: Date.now()
  };
  
  assertThrows(
    () => receiver.receiveTemplateEvent(invalidEvent),
    Error,
    "Invalid template"
  );
});

Deno.test("handleConcurrentTemplateEvents_detects_conflicts", () => {
  const handler = new ConcurrentEventHandler();
  
  const event1: TemplateEvent = {
    id: "evt_1",
    template: "UPDATE_USER",
    params: { id: "u1", name: "Alice" },
    timestamp: 1000,
    clientId: "client1"
  };
  
  const event2: TemplateEvent = {
    id: "evt_2",
    template: "UPDATE_USER",
    params: { id: "u1", name: "Bob" },
    timestamp: 1001,
    clientId: "client2"
  };
  
  const conflicts = handler.detectConflicts([event1, event2]);
  assertEquals(conflicts.length, 1);
  assertEquals(conflicts[0].type, "CONCURRENT_UPDATE");
});

// ========== 8. セキュリティ ==========

Deno.test("executeTemplate_with_sql_injection_attempt_sanitizes", () => {
  const executor = new SecureTemplateExecutor();
  
  const maliciousParams = {
    id: "u1",
    name: "Alice'; DROP TABLE users; --"
  };
  
  const sanitized = executor.sanitizeParams("CREATE_USER", maliciousParams);
  assert(!sanitized.name.includes("DROP"));
  assert(!sanitized.name.includes(";"));
});

Deno.test("executeTemplate_with_unauthorized_template_denies", () => {
  const executor = new SecureTemplateExecutor();
  
  assertThrows(
    () => executor.executeTemplate("DELETE_ALL_USERS", {}),
    Error,
    "Unauthorized template"
  );
});

Deno.test("validateChecksum_with_tampered_event_fails", () => {
  const validator = new ChecksumValidator();
  
  const event: TemplateEvent = {
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1", name: "Alice" },
    timestamp: 1000,
    checksum: "abc123"
  };
  
  // Tamper with event
  event.params.name = "Bob";
  
  const isValid = validator.validateChecksum(event);
  assertEquals(isValid, false);
});

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== Template-based Event Sourcing - TDD Red Phase ===");
  console.log("All tests should fail initially");
}