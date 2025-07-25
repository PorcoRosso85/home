/**
 * Test for MetricsCollectorImpl move to operations/
 * operations/への移動テスト
 */

import { assertEquals } from "https://deno.land/std@0.221.0/assert/mod.ts";
import { MetricsCollectorImpl } from "../operations/metrics_collector.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";

Deno.test("MetricsCollectorImpl can be imported from operations/", () => {
  const collector = new MetricsCollectorImpl();
  
  const event: TemplateEvent = {
    id: "event1",
    template: "createUser",
    params: { name: "Test" },
    timestamp: Date.now()
  };
  
  collector.trackEvent(event);
  
  const stats = collector.getStats();
  assertEquals(stats.totalEvents, 1);
  assertEquals(stats.eventTypes["createUser"], 1);
  assertEquals(stats.errors, 0);
});

Deno.test("MetricsCollectorImpl tracks multiple events", () => {
  const collector = new MetricsCollectorImpl();
  
  collector.trackEvent({
    id: "event1",
    template: "createUser",
    params: { name: "User1" },
    timestamp: Date.now()
  });
  
  collector.trackEvent({
    id: "event2",
    template: "createPost",
    params: { content: "Post1" },
    timestamp: Date.now()
  });
  
  collector.trackEvent({
    id: "event3",
    template: "createUser",
    params: { name: "User2" },
    timestamp: Date.now()
  });
  
  const stats = collector.getStats();
  assertEquals(stats.totalEvents, 3);
  assertEquals(stats.eventTypes["createUser"], 2);
  assertEquals(stats.eventTypes["createPost"], 1);
});