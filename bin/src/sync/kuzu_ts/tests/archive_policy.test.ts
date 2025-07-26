/**
 * Archive Policy Tests
 * Tests for identifying events that should be archived based on age
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type { TemplateEvent } from "../types.ts";

// The function to be implemented
// This import will fail initially (RED phase)
import { shouldArchive } from "../storage/archive_policy.ts";

// Helper function to create a test event with specific timestamp
function createTestEvent(timestamp: number): TemplateEvent {
  return {
    id: crypto.randomUUID(),
    template: "test_template",
    params: { test: true },
    timestamp,
    clientId: "test-client",
    checksum: "mock-checksum"
  };
}

// Helper function to create a date that is N days ago from current time
function daysAgo(days: number, currentTime: number): number {
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  return currentTime - (days * millisecondsPerDay);
}

Deno.test("shouldArchive - event exactly 30 days old should be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const thirtyDaysAgo = daysAgo(30, currentTime);
  const event = createTestEvent(thirtyDaysAgo);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, true, "Event exactly 30 days old should be archived");
});

Deno.test("shouldArchive - event 31 days old should be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const thirtyOneDaysAgo = daysAgo(31, currentTime);
  const event = createTestEvent(thirtyOneDaysAgo);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, true, "Event 31 days old should be archived");
});

Deno.test("shouldArchive - event 29 days 23 hours 59 minutes old should NOT be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  const millisecondsPerMinute = 60 * 1000;
  
  // 29 days, 23 hours, 59 minutes ago
  const almostThirtyDaysAgo = currentTime - (29 * millisecondsPerDay) - (23 * 60 * millisecondsPerMinute) - (59 * millisecondsPerMinute);
  const event = createTestEvent(almostThirtyDaysAgo);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, false, "Event less than 30 days old should NOT be archived");
});

Deno.test("shouldArchive - event 1 day old should NOT be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const oneDayAgo = daysAgo(1, currentTime);
  const event = createTestEvent(oneDayAgo);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, false, "Event 1 day old should NOT be archived");
});

Deno.test("shouldArchive - event 100 days old should be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const hundredDaysAgo = daysAgo(100, currentTime);
  const event = createTestEvent(hundredDaysAgo);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, true, "Event 100 days old should be archived");
});

Deno.test("shouldArchive - event with future timestamp should NOT be archived", () => {
  // Arrange
  const currentTime = Date.now();
  const futureTime = currentTime + (24 * 60 * 60 * 1000); // 1 day in the future
  const event = createTestEvent(futureTime);

  // Act
  const result = shouldArchive(event, currentTime);

  // Assert
  assertEquals(result, false, "Event with future timestamp should NOT be archived");
});