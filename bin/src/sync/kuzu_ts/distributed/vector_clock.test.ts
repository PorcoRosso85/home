/**
 * Vector Clock Tests
 * ベクタークロックの分散順序付けテスト
 * 
 * Vector clocks ensure causality tracking across multiple nodes in a distributed system.
 * Each node maintains its own logical clock and tracks the state of other nodes.
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { VectorClock } from "./vector_clock.ts";

Deno.test("VectorClock - should initialize with node ID", () => {
  const clock = new VectorClock("node1");
  
  // Clock should start at 0 for the local node
  assertEquals(clock.getValue("node1"), 0);
  
  // Should return node ID
  assertEquals(clock.getNodeId(), "node1");
});

Deno.test("VectorClock - should increment local clock", () => {
  const clock = new VectorClock("node1");
  
  // Increment local clock
  clock.increment();
  assertEquals(clock.getValue("node1"), 1);
  
  // Multiple increments
  clock.increment();
  clock.increment();
  assertEquals(clock.getValue("node1"), 3);
});

Deno.test("VectorClock - should merge clocks from other nodes", () => {
  const clock1 = new VectorClock("node1");
  const clock2 = new VectorClock("node2");
  
  // Set up initial states
  clock1.increment(); // node1: 1
  clock2.increment(); // node2: 1
  clock2.increment(); // node2: 2
  
  // Merge clock2 into clock1
  clock1.merge(clock2);
  
  // clock1 should have max values from both clocks
  assertEquals(clock1.getValue("node1"), 1);
  assertEquals(clock1.getValue("node2"), 2);
  
  // Original clock2 should be unchanged
  assertEquals(clock2.getValue("node1"), 0);
  assertEquals(clock2.getValue("node2"), 2);
});

Deno.test("VectorClock - should detect happened-before relationship", () => {
  const clock1 = new VectorClock("node1");
  const clock2 = new VectorClock("node2");
  
  // clock1 happens before clock2 if all clock1 values <= clock2 values
  // and at least one is strictly less
  clock1.increment(); // node1: 1
  
  // Copy state from clock1 to clock2 (simulating message passing)
  clock2.merge(clock1);
  clock2.increment(); // node2: 1
  
  // clock1 happened before clock2
  assert(clock1.happenedBefore(clock2));
  assert(!clock2.happenedBefore(clock1));
});

Deno.test("VectorClock - should detect concurrent events", () => {
  const clock1 = new VectorClock("node1");
  const clock2 = new VectorClock("node2");
  
  // Independent increments create concurrent events
  clock1.increment(); // node1: 1
  clock2.increment(); // node2: 1
  
  // Neither happened before the other
  assert(!clock1.happenedBefore(clock2));
  assert(!clock2.happenedBefore(clock1));
  
  // They are concurrent
  assert(clock1.isConcurrent(clock2));
  assert(clock2.isConcurrent(clock1));
});

Deno.test("VectorClock - should handle complex causality chains", () => {
  const clock1 = new VectorClock("node1");
  const clock2 = new VectorClock("node2");
  const clock3 = new VectorClock("node3");
  
  // node1 sends to node2
  clock1.increment(); // node1: 1
  clock2.merge(clock1);
  clock2.increment(); // node2: 1, knows node1: 1
  
  // node2 sends to node3
  clock3.merge(clock2);
  clock3.increment(); // node3: 1, knows node1: 1, node2: 1
  
  // Check causality
  assert(clock1.happenedBefore(clock3));
  assert(clock2.happenedBefore(clock3));
  assert(!clock3.happenedBefore(clock1));
  assert(!clock3.happenedBefore(clock2));
});

Deno.test("VectorClock - should provide clock snapshot", () => {
  const clock = new VectorClock("node1");
  
  clock.increment();
  // Simulate receiving info about other nodes
  clock.update("node2", 3);
  clock.update("node3", 2);
  
  const snapshot = clock.toSnapshot();
  
  assertEquals(snapshot, {
    node1: 1,
    node2: 3,
    node3: 2
  });
});

Deno.test("VectorClock - should create from snapshot", () => {
  const snapshot = {
    node1: 5,
    node2: 3,
    node3: 7
  };
  
  const clock = VectorClock.fromSnapshot("node1", snapshot);
  
  assertEquals(clock.getValue("node1"), 5);
  assertEquals(clock.getValue("node2"), 3);
  assertEquals(clock.getValue("node3"), 7);
  assertEquals(clock.getNodeId(), "node1");
});

Deno.test("VectorClock - should compare for equality", () => {
  const clock1 = new VectorClock("node1");
  const clock2 = new VectorClock("node2");
  
  // Initially equal (all zeros)
  assert(clock1.equals(clock2));
  
  // After increment, not equal
  clock1.increment();
  assert(!clock1.equals(clock2));
  
  // Make clock2 match clock1
  clock2.update("node1", 1);
  assert(clock1.equals(clock2));
});

Deno.test("VectorClock - should handle missing node entries gracefully", () => {
  const clock = new VectorClock("node1");
  
  // Getting value for unknown node should return 0
  assertEquals(clock.getValue("unknown-node"), 0);
  
  // Should be able to update unknown nodes
  clock.update("node2", 5);
  assertEquals(clock.getValue("node2"), 5);
});