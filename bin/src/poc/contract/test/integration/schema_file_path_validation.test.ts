/**
 * JSON Schemaファイルパス必須化テスト
 * 
 * テスト対象:
 * 1. Provider登録時にinput/outputスキーマファイルパスが必須
 * 2. Consumer登録時にexpects.input/outputスキーマファイルパスが必須
 * 3. ファイルパスバリデーション（存在確認、読み取り可能性、JSON妥当性）
 */

import { assert, assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { handler } from "../../src/main.ts";

const RPC_URL = "http://localhost:8000/rpc";

// テスト用スキーマファイルを作成
async function setupTestSchemaFiles() {
  const testDir = await Deno.makeTempDir();
  
  // 有効なスキーマファイル
  const validInputSchema = {
    type: "object",
    properties: {
      city: { type: "string" }
    },
    required: ["city"]
  };
  
  const validOutputSchema = {
    type: "object",
    properties: {
      temperature: { type: "number" },
      humidity: { type: "number" }
    },
    required: ["temperature"]
  };
  
  await Deno.writeTextFile(
    `${testDir}/input.schema.json`,
    JSON.stringify(validInputSchema)
  );
  
  await Deno.writeTextFile(
    `${testDir}/output.schema.json`,
    JSON.stringify(validOutputSchema)
  );
  
  // 不正なJSONファイル
  await Deno.writeTextFile(
    `${testDir}/invalid.json`,
    "{ invalid json"
  );
  
  return testDir;
}

Deno.test("スキーマファイルパス必須化: Provider/Consumer登録", async (t) => {
  // Start server
  const controller = new AbortController();
  const server = serve(handler, { 
    port: 8000,
    signal: controller.signal,
    onListen: () => console.log("Test server started")
  });
  await delay(100);
  
  const testDir = await setupTestSchemaFiles();
  
  try {
    
  // 1. Provider登録: スキーマファイルパスなし
  await t.step("Provider登録時にスキーマファイルパスが欠落", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "weather/v1",
          endpoint: "http://weather:8080"
          // inputSchemaPath, outputSchemaPath が欠落
        },
        id: 1
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("inputSchemaPath"));
  });

  // 2. Provider登録: 有効なスキーマファイルパス
  await t.step("Provider登録時に有効なスキーマファイルパスを提供", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "weather/v1",
          inputSchemaPath: `${testDir}/input.schema.json`,
          outputSchemaPath: `${testDir}/output.schema.json`,
          endpoint: "http://weather:8080"
        },
        id: 2
      })
    });
    
    const result = await response.json();
    assertEquals(result.result.status, "registered");
    assertEquals(result.result.provider, "weather/v1");
    // スキーマが正しく読み込まれたことを確認
    assert(result.result.schema);
    assert(result.result.schema.input.properties.city);
    assert(result.result.schema.output.properties.temperature);
  });

  // 3. Provider登録: 存在しないファイルパス
  await t.step("Provider登録時に存在しないファイルパスを指定", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "weather/v2",
          inputSchemaPath: "/nonexistent/input.schema.json",
          outputSchemaPath: "/nonexistent/output.schema.json",
          endpoint: "http://weather:8080"
        },
        id: 3
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32603); // Internal error
    assert(result.error.data.detail.includes("Schema file not found"));
  });

  // 4. Provider登録: 不正なJSONファイル
  await t.step("Provider登録時に不正なJSONファイルを指定", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "weather/v3",
          inputSchemaPath: `${testDir}/invalid.json`,
          outputSchemaPath: `${testDir}/output.schema.json`,
          endpoint: "http://weather:8080"
        },
        id: 4
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32603); // Internal error
    assert(result.error.data.detail.includes("Invalid JSON"));
  });

  // 5. Consumer登録: expectsスキーマファイルパスなし
  await t.step("Consumer登録時にexpectsスキーマファイルパスが欠落", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "consumer",
          uri: "dashboard/v1"
          // expectsInputSchemaPath, expectsOutputSchemaPath が欠落
        },
        id: 5
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32602); // Invalid params
    assert(result.error.data.detail.includes("expectsInputSchemaPath"));
  });

  // 6. Consumer登録: 有効なexpectsスキーマファイルパス
  await t.step("Consumer登録時に有効なexpectsスキーマファイルパスを提供", async () => {
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "consumer",
          uri: "dashboard/v1",
          expectsInputSchemaPath: `${testDir}/input.schema.json`,
          expectsOutputSchemaPath: `${testDir}/output.schema.json`
        },
        id: 6
      })
    });
    
    const result = await response.json();
    assertEquals(result.result.status, "registered");
    assertEquals(result.result.consumer, "dashboard/v1");
    // expectsスキーマが正しく読み込まれたことを確認
    assert(result.result.expects);
    assert(result.result.expects.input.properties.city);
    assert(result.result.expects.output.properties.temperature);
  });

  // 7. 相対パスの扱い
  await t.step("相対パスを絶対パスに変換して処理", async () => {
    // テスト用の相対パス用スキーマファイルを作成
    await Deno.writeTextFile(
      "./test_input.schema.json",
      JSON.stringify({ type: "object", properties: { test: { type: "string" } } })
    );
    await Deno.writeTextFile(
      "./test_output.schema.json",
      JSON.stringify({ type: "object", properties: { result: { type: "string" } } })
    );
    
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "test/v1",
          inputSchemaPath: "./test_input.schema.json",
          outputSchemaPath: "./test_output.schema.json",
          endpoint: "http://test:8080"
        },
        id: 7
      })
    });
    
    const result = await response.json();
    assertEquals(result.result.status, "registered");
    
    // クリーンアップ
    await Deno.remove("./test_input.schema.json");
    await Deno.remove("./test_output.schema.json");
  });

  // 8. スキーマバリデーション
  await t.step("無効なJSON Schemaフォーマット", async () => {
    // 無効なスキーマファイルを作成
    await Deno.writeTextFile(
      `${testDir}/invalid_schema.json`,
      JSON.stringify({ 
        // type指定なし、propertiesなしの無効なスキーマ
        invalidField: "This is not a valid JSON Schema" 
      })
    );
    
    const response = await fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "contract.register",
        params: {
          type: "provider",
          uri: "invalid/v1",
          inputSchemaPath: `${testDir}/invalid_schema.json`,
          outputSchemaPath: `${testDir}/output.schema.json`,
          endpoint: "http://invalid:8080"
        },
        id: 8
      })
    });
    
    const result = await response.json();
    assertEquals(result.error.code, -32603); // Internal error
    assert(result.error.data.detail.includes("Invalid JSON Schema"));
  });

  } finally {
    // クリーンアップ
    await Deno.remove(testDir, { recursive: true });
    controller.abort();
    await server;
  }
});