/**
 * E2E Integration Test: Contract Service JSON-RPC2版
 * 
 * テスト対象機能:
 * 1. 契約登録（Provider/Consumer）
 * 2. 自動マッチング（スキーマ互換性判定）
 * 3. データ変換（フィールドマッピング）
 * 4. ルーティング（適切なProviderへの転送）
 * 6. エラーハンドリング（不正な契約、通信エラー）
 */

import { assert, assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { handler } from "../../src/main.ts";

const CONTRACT_SERVICE_URL = "http://localhost:8000/rpc";

// JSON-RPC2 helper
async function rpcCall(method: string, params: any, id = 1) {
  const response = await fetch(CONTRACT_SERVICE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method,
      params,
      id
    })
  });
  
  const result = await response.json();
  if (result.error) {
    throw new Error(`RPC Error ${result.error.code}: ${result.error.message}`);
  }
  return result.result;
}

Deno.test("E2E: Contract Service JSON-RPC2 主要機能統合テスト", async (t) => {
  // Declare variables outside try block
  let testDir: string = "";
  let weatherService: any;
  
  // Start Contract Service within test
  const controller = new AbortController();
  const contractService = serve(handler, { 
    port: 8000,
    signal: controller.signal,
    onListen: () => console.log("Test server started on port 8000")
  });
  await delay(100); // Wait for server startup
  
  try {
  // Create temporary directory for schema files
  testDir = await Deno.makeTempDir();
  
  // Create Weather Service schema files
  await Deno.writeTextFile(
    `${testDir}/weather-input.schema.json`,
    JSON.stringify({
      type: "object",
      properties: {
        location: { type: "string" }
      },
      required: ["location"]
    })
  );
  await Deno.writeTextFile(
    `${testDir}/weather-output.schema.json`,
    JSON.stringify({
      type: "object",
      properties: {
        temperature: { type: "number" },
        humidity: { type: "number" },
        location: { type: "string" }
      },
      required: ["temperature", "humidity", "location"]
    })
  );
  
  // Create Dashboard schema files
  await Deno.writeTextFile(
    `${testDir}/dashboard-expects-input.schema.json`,
    JSON.stringify({
      type: "object",
      properties: {
        temp: { type: "number" },
        humid: { type: "number" },
        city: { type: "string" }
      },
      required: ["temp", "humid", "city"]
    })
  );
  await Deno.writeTextFile(
    `${testDir}/dashboard-expects-output.schema.json`,
    JSON.stringify({
      type: "object",
      properties: {
        city: { type: "string" }
      },
      required: ["city"]
    })
  );

  // Step 1: Weather Service（Provider）の契約登録
  await t.step("Weather Serviceを登録", async () => {
    const result = await rpcCall("contract.register", {
      type: "provider",
      uri: "services/weather/v1",
      inputSchemaPath: `${testDir}/weather-input.schema.json`,
      outputSchemaPath: `${testDir}/weather-output.schema.json`,
      endpoint: "http://localhost:9001/weather"
    });

    assertEquals(result.status, "registered");
    assertEquals(result.provider, "services/weather/v1");
    assert(Array.isArray(result.matches), "Should return matches array");
  });

  // Step 2: Dashboard（Consumer）の契約登録
  await t.step("Dashboard Consumerを登録", async () => {
    const result = await rpcCall("contract.register", {
      type: "consumer",
      uri: "ui/dashboard/v2",
      expectsInputSchemaPath: `${testDir}/dashboard-expects-output.schema.json`,
      expectsOutputSchemaPath: `${testDir}/dashboard-expects-input.schema.json`
    }, 2);

    assertEquals(result.status, "registered");
    assertEquals(result.consumer, "ui/dashboard/v2");
    assert(Array.isArray(result.providers), "Should return providers array");
    assertEquals(result.providers.length, 1);
    assertEquals(result.providers[0].uri, "services/weather/v1");
  });


  // Step 4: 変換テスト（ドライラン）
  await t.step("変換のドライランテスト", async () => {
    const result = await rpcCall("contract.test", {
      from: "ui/dashboard/v2",
      to: "services/weather/v1",
      testData: { city: "Tokyo" },
      dryRun: true
    }, 4);

    assert(Array.isArray(result.steps));
    assertEquals(result.steps[0].step, "input");
    assertEquals(result.steps[0].data, { city: "Tokyo" });
    assertEquals(result.steps[1].step, "transformed");
    assertEquals(result.steps[1].data, { location: "Tokyo" });
    assertEquals(result.steps[3].step, "output");
    assertEquals(result.steps[3].data.city, "Tokyo");
  });

  // Step 5: エラーハンドリングテスト
  await t.step("不正な契約登録のエラーハンドリング", async () => {
    try {
      await rpcCall("contract.register", {
        type: "provider",
        uri: "invalid/service",
        // Missing required inputSchemaPath and outputSchemaPath
      }, 5);
      assert(false, "Should throw error");
    } catch (error) {
      assert(error instanceof Error);
      assert(error.message.includes("-32602")); // Invalid params error code
    }
  });

  // Step 6: 実際の通信テスト
  // TODO: 実際のWeather Serviceの起動が必要
  // weatherService = await startRealWeatherService();
  
  try {
    await t.step("Dashboard → Contract Service → Weather Service の通信", async () => {
      const result = await rpcCall("contract.call", {
        from: "ui/dashboard/v2",
        data: { city: "Tokyo" }
      }, 6);

      // Check response structure
      assert(result.data);
      assert(result.meta);
      
      // Check transformed data
      assertEquals(result.data.temp, 25.5);
      assertEquals(result.data.humid, 60);
      assertEquals(result.data.city, "Tokyo");
      
      // Check metadata
      assertEquals(result.meta.transformApplied, true);
      assert(typeof result.meta.latency === "number");
    });

  } finally {
    // クリーンアップ
    await weatherService.shutdown();
  }

  // Step 7: Provider不在エラー
  await t.step("Provider通信エラー時のエラーハンドリング", async () => {
    try {
      await rpcCall("contract.call", {
        from: "ui/dashboard/v2",
        data: { city: "Tokyo" }
      }, 7);
      assert(false, "Should throw error");
    } catch (error) {
      assert(error instanceof Error);
      assert(error.message.includes("-32001")); // No provider error code
    }
  });

  // Step 8: バッチリクエストテスト
  await t.step("バッチリクエストの処理", async () => {
    const response = await fetch(CONTRACT_SERVICE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([
        {
          jsonrpc: "2.0",
          method: "contract.register",
          params: { 
            type: "provider", 
            uri: "services/geocode/v1", 
            inputSchemaPath: `${testDir}/weather-input.schema.json`,
            outputSchemaPath: `${testDir}/weather-output.schema.json`,
            endpoint: "http://localhost:9003" 
          },
          id: 1
        },
        {
          jsonrpc: "2.0",
          method: "contract.test",
          params: {
            from: "ui/dashboard/v2",
            to: "services/weather/v1",
            testData: { city: "Osaka" },
            dryRun: true
          },
          id: 2
        }
      ])
    });

    const results = await response.json();
    assertEquals(results.length, 2);
    assertEquals(results[0].id, 1);
    assertEquals(results[1].id, 2);
    assertEquals(results[0].result.status, "registered");
    assertEquals(results[1].result.steps[0].data.city, "Osaka");
  });
  
  } finally {
    // Cleanup weather service
    if (weatherService) {
      weatherService.shutdown();
    }
    
    // Cleanup temporary directory
    if (testDir) {
      await Deno.remove(testDir, { recursive: true });
    }
    
    // Cleanup Contract Service
    controller.abort();
    await contractService;
  }
});

// TODO: 実際のWeather Service起動ヘルパーが必要
// async function startRealWeatherService() {
//   // 実際のサービスを起動する実装
// }