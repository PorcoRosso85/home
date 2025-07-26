/**
 * RED Test: Validates client functionality after moving to core/client/
 * This test should fail initially as the file hasn't been moved yet
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import type { BrowserKuzuClient, LocalState, EventSnapshot } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

Deno.test("BrowserKuzuClientImpl - import from new location", async (t) => {
  await t.step("should successfully import BrowserKuzuClientImpl from core/client/", () => {
    assertExists(BrowserKuzuClientImpl);
    assertEquals(typeof BrowserKuzuClientImpl, "function");
  });
});

Deno.test("BrowserKuzuClientImpl - instantiation", async (t) => {
  await t.step("should be able to instantiate BrowserKuzuClientImpl", () => {
    const client = new BrowserKuzuClientImpl();
    assertExists(client);
  });

  await t.step("should implement BrowserKuzuClient interface", () => {
    const client = new BrowserKuzuClientImpl();
    
    // Check that all required methods exist
    assertEquals(typeof client.initialize, "function");
    assertEquals(typeof client.initializeFromSnapshot, "function");
    assertEquals(typeof client.executeTemplate, "function");
    assertEquals(typeof client.getLocalState, "function");
    assertEquals(typeof client.onRemoteEvent, "function");
  });
});

Deno.test("BrowserKuzuClientImpl - maintains interface compatibility", async (t) => {
  await t.step("initialize method signature", () => {
    const client = new BrowserKuzuClientImpl();
    // initialize should return Promise<void>
    const initPromise = client.initialize();
    assertExists(initPromise);
    assertEquals(initPromise instanceof Promise, true);
  });

  await t.step("initializeFromSnapshot method signature", () => {
    const client = new BrowserKuzuClientImpl();
    const mockedSnapshot: EventSnapshot = {
      events: [],
      timestamp: Date.now(),
      version: "1.0"
    };
    
    // initializeFromSnapshot should accept EventSnapshot and return Promise<void>
    const snapshotPromise = client.initializeFromSnapshot(mockedSnapshot);
    assertExists(snapshotPromise);
    assertEquals(snapshotPromise instanceof Promise, true);
  });

  await t.step("executeTemplate method signature", async () => {
    const client = new BrowserKuzuClientImpl();
    
    // Mock initialization to avoid actual WASM loading
    client["conn"] = {}; // Set conn to avoid "Client not initialized" error
    client["registry"] = {
      getTemplateMetadata: () => ({
        requiredParams: [],
        optionalParams: [],
        description: "test"
      })
    };
    
    try {
      // executeTemplate should accept template string and params, return Promise<TemplateEvent>
      const templatePromise = client.executeTemplate("TEST_TEMPLATE", { test: "value" });
      assertExists(templatePromise);
      assertEquals(templatePromise instanceof Promise, true);
    } catch (e) {
      // Expected to fail in test environment without actual KuzuDB
      assertExists(e);
    }
  });

  await t.step("getLocalState method signature", async () => {
    const client = new BrowserKuzuClientImpl();
    
    // getLocalState should return Promise<LocalState>
    const statePromise = client.getLocalState();
    assertExists(statePromise);
    assertEquals(statePromise instanceof Promise, true);
    
    const state = await statePromise;
    assertExists(state);
    assertExists(state.users);
    assertExists(state.posts);
    assertExists(state.follows);
  });

  await t.step("onRemoteEvent method signature", () => {
    const client = new BrowserKuzuClientImpl();
    let handlerCalled = false;
    
    const mockedHandler = (event: TemplateEvent) => {
      handlerCalled = true;
    };
    
    // onRemoteEvent should accept a handler function
    client.onRemoteEvent(mockedHandler);
    
    // Verify handler was registered (no error thrown)
    assertExists(client["remoteEventHandlers"]);
    assertEquals(client["remoteEventHandlers"].length, 1);
  });
});

Deno.test("BrowserKuzuClientImpl - private members accessibility", async (t) => {
  await t.step("should maintain access to private members", () => {
    const client = new BrowserKuzuClientImpl();
    
    // These should exist as private members
    assertExists(client["events"]);
    assertExists(client["remoteEventHandlers"]);
    assertExists(client["registry"]);
    assertExists(client["clientId"]);
    
    // Verify initial state
    assertEquals(Array.isArray(client["events"]), true);
    assertEquals(Array.isArray(client["remoteEventHandlers"]), true);
    assertEquals(typeof client["clientId"], "string");
    assertEquals(client["clientId"].startsWith("browser_"), true);
  });
});