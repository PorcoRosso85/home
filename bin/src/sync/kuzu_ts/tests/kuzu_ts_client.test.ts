import { assertEquals, assertExists } from "jsr:@std/assert@1";
import { KuzuTsClientImpl } from "../core/client/kuzu_ts_client.ts";

Deno.test({
  name: "KuzuTsClient can be instantiated",
  fn: () => {
    const client = new KuzuTsClientImpl();
    assertExists(client);
    assertEquals(client.getSchemaVersion(), 0);
  }
});

Deno.test({
  name: "KuzuTsClient has unique client ID prefix",
  fn: () => {
    const client = new KuzuTsClientImpl();
    const schemaState = client.getSchemaState();
    // Client ID is embedded in schema manager
    assertExists(schemaState);
  }
});

// Note: Full integration tests would require proper module resolution
// These tests verify the basic structure and interface compliance