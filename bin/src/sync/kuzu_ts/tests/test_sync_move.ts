/**
 * Test for ConflictResolverImpl move to core/sync/
 * core/sync/への移動テスト
 */

import { assertEquals } from "https://deno.land/std@0.221.0/assert/mod.ts";
import { ConflictResolverImpl } from "../core/sync/conflict_resolver.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

Deno.test("ConflictResolverImpl can be imported from core/sync/", () => {
  const resolver = new ConflictResolverImpl();
  
  const event: TemplateEvent = {
    id: "event1",
    template: "template1",
    params: { name: "Test" },
    timestamp: Date.now()
  };
  
  const resolution = resolver.resolve([event]);
  
  assertEquals(resolution.strategy, "NO_CONFLICT");
  assertEquals(resolution.winner, event);
  assertEquals(resolution.conflicts.length, 0);
});

Deno.test("ConflictResolverImpl resolves conflicts with Last Write Wins", () => {
  const resolver = new ConflictResolverImpl();
  
  const event1: TemplateEvent = {
    id: "event1",
    template: "template1",
    params: { name: "First" },
    timestamp: 1000
  };
  
  const event2: TemplateEvent = {
    id: "event2",
    template: "template1",
    params: { name: "Second" },
    timestamp: 2000
  };
  
  const resolution = resolver.resolve([event1, event2]);
  
  assertEquals(resolution.strategy, "LAST_WRITE_WINS");
  assertEquals(resolution.winner, event2);
  assertEquals(resolution.conflicts.length, 1);
  assertEquals(resolution.conflicts[0], event1);
});