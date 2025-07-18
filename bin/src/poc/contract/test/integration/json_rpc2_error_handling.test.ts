/**
 * JSON-RPC2 異常系テスト
 * 
 * テスト対象:
 * 1. JSON-RPC2プロトコル違反
 * 2. 契約書（スキーマ）なしでの登録試行
 * 3. 不正なメソッド呼び出し
 * 4. パラメータ不足・型違い
 * 5. バッチリクエストでの部分的失敗
 */

import { assert, assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { handler } from "../../src/main.ts";

const RPC_URL = "http://localhost:8000/rpc";

Deno.test("異常系: JSON-RPC2 プロトコルエラーハンドリング", async (t) => {
  // Create temporary schema files for batch test
  await Deno.writeTextFile("/tmp/test-input.json", JSON.stringify({ type: "object", properties: {} }));
  await Deno.writeTextFile("/tmp/test-output.json", JSON.stringify({ type: "object", properties: {} }));
  
  // Start server
  const controller = new AbortController();
  const server = serve(handler, { 
    port: 8000,
    signal: controller.signal,
    onListen: () => console.log("Test server started")
  });
  await delay(100);
  
  try {
    
  // 1. jsonrpcバージョンが不正
  await t.step("jsonrpcバージョンが2.0でない場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "1.0",  // 不正なバージョン
        method: "contract.register",
        params: {},
        id: 1
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32600); // Invalid Request
    assertEquals(result.error.message, "Invalid Request");
  });

  // 2. methodフィールドが欠落
  await t.step("methodフィールドが存在しない場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        params: {},
        id: 2
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32600); // Invalid Request
  });

  // 3. 存在しないメソッドの呼び出し
  await t.step("存在しないメソッドを呼び出した場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.invalid_method",
        params: {},
        id: 3
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32601); // Method not found
    assertEquals(result.error.message, "Method not found");
  });

  // 4. 不正なJSON
  await t.step("パースできないJSONを送信した場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{ invalid json"
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32700); // Parse error
    assertEquals(result.error.message, "Parse error");
  });

  // 5. 契約書なしでのProvider登録
  await t.step("Providerが契約書なしで登録しようとした場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "services/no-contract",
          // inputSchemaPath and outputSchemaPath are missing
        },
        id: 5
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("inputSchemaPath"));
  });

  // 6. 契約書なしでのConsumer登録
  await t.step("Consumerが契約書なしで登録しようとした場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "consumer",
          uri: "ui/no-expects"
          // expectsInputSchemaPath and expectsOutputSchemaPath are missing
        },
        id: 6
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("expectsInputSchemaPath"));
  });

  // 7. 不正な型でのパラメータ
  await t.step("schemaPathが不正な場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "services/bad-schema",
          inputSchemaPath: 123,  // Should be string
          outputSchemaPath: "output.json"
        },
        id: 7
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("inputSchemaPath must be a string"));
  });

  // 8. 必須パラメータ不足
  await t.step("typeパラメータが欠落している場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          uri: "services/no-type",
          inputSchemaPath: "input.json",
          outputSchemaPath: "output.json"
          // typeが欠落
        },
        id: 8
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("type"));
  });

  // 9. callメソッドでfromパラメータなし
  await t.step("contract.callでfromが指定されていない場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.call",
        params: {
          data: { city: "Tokyo" }
          // fromが欠落
        },
        id: 9
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("from"));
  });

  // 10. バッチリクエストで一部が失敗
  await t.step("バッチリクエストで成功と失敗が混在する場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([
        {
          jsonrpc: "2.0",
          method: "contract.register",
          params: {
            type: "provider",
            uri: "services/batch-ok",
            inputSchemaPath: "/tmp/test-input.json",
            outputSchemaPath: "/tmp/test-output.json",
            endpoint: "http://localhost:9999"
          },
          id: "batch-1"
        },
        {
          jsonrpc: "2.0",
          method: "invalid.method",  // 不正なメソッド
          params: {},
          id: "batch-2"
        },
        {
          jsonrpc: "1.0",  // 不正なバージョン
          method: "contract.register",
          params: {},
          id: "batch-3"
        }
      ])
    });
    
    const results = await response.json();
    assertEquals(results.length, 3);
    
    // 1つ目は成功
    assertEquals(results[0].id, "batch-1");
    assert(results[0].result);
    assertEquals(results[0].result.status, "registered");
    
    // 2つ目は失敗（メソッドなし）
    assertEquals(results[1].id, "batch-2");
    assert(results[1].error);
    assertEquals(results[1].error.code, -32601);
    
    // 3つ目は失敗（プロトコルエラー）
    assertEquals(results[2].id, "batch-3");
    assert(results[2].error);
    assertEquals(results[2].error.code, -32600);
  });

  // 11. 空のバッチリクエスト
  await t.step("空の配列をバッチリクエストとして送信した場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([])
    });
    
    const results = await response.json();
    assert(Array.isArray(results));
    assertEquals(results.length, 0);
  });

  // 12. 通知リクエスト（idなし）の処理
  await t.step("通知リクエスト（idなし）でエラーが発生した場合", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          // 不正なパラメータでエラーを誘発
          uri: "test"
          // Missing required schema paths
        }
        // idフィールドなし = 通知
      })
    });
    
    const result = await response.json();
    // 通知の場合でもエラーレスポンスは返る
    assert(result.error);
    assertEquals(result.id, null);
  });

  } finally {
    controller.abort();
    await server;
    
    // Clean up temporary files
    try {
      await Deno.remove("/tmp/test-input.json");
      await Deno.remove("/tmp/test-output.json");
    } catch {
      // Ignore cleanup errors
    }
  }
});