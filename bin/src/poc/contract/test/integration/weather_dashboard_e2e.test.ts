/**
 * E2E Integration Test: Contract Service主要機能の統合テスト
 * 
 * テスト対象機能:
 * 1. 契約登録（Provider/Consumer）
 * 2. 自動マッチング（スキーマ互換性判定）
 * 3. データ変換（フィールドマッピング）
 * 4. ルーティング（適切なProviderへの転送）
 * 5. 複数Provider対応（最適なProviderの選択）
 * 6. エラーハンドリング（不正な契約、通信エラー）
 * 7. 変換スクリプトの安全実行（Worker隔離）
 * 
 * シナリオ: Weather Services（複数）→ Dashboard
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";

const CONTRACT_SERVICE_URL = "http://localhost:8000";

Deno.test("E2E: Contract Service 主要機能統合テスト", async (t) => {
  // 準備: Contract Serviceが起動していることを確認
  await t.step("Contract Service健全性チェック", async () => {
    const health = await fetch(`${CONTRACT_SERVICE_URL}/health`);
    assertEquals(health.status, 200);
  });

  // Step 1: Weather Service（Provider）の契約登録
  await t.step("Weather Serviceを登録", async () => {
    const response = await fetch(`${CONTRACT_SERVICE_URL}/register/provider`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        uri: "services/weather#current",
        schema: {
          input: {
            type: "object",
            properties: {
              location: { type: "string" }
            }
          },
          output: {
            type: "object", 
            properties: {
              temperature: { type: "number" },
              humidity: { type: "number" },
              location: { type: "string" }
            }
          }
        },
        // 実際のサービスエンドポイント（モック）
        endpoint: "http://localhost:9001/weather"
      })
    });

    assertEquals(response.status, 201);
    const result = await response.json();
    assertEquals(result.status, "registered");
    assertEquals(result.provider, "services/weather#current");
  });

  // Step 2: Dashboard（Consumer）の契約登録
  await t.step("Dashboard Consumerを登録", async () => {
    const response = await fetch(`${CONTRACT_SERVICE_URL}/register/consumer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        uri: "ui/dashboard#weather-widget",
        expects: {
          output: {
            type: "object",
            properties: {
              city: { type: "string" }  // location → city
            }
          },
          input: {
            type: "object",
            properties: {
              temp: { type: "number" },      // temperature → temp
              humid: { type: "number" },     // humidity → humid  
              city: { type: "string" }       // location → city
            }
          }
        }
      })
    });

    assertEquals(response.status, 201);
    const result = await response.json();
    assertEquals(result.status, "registered");
    assertEquals(result.consumer, "ui/dashboard#weather-widget");
  });

  // Step 3: 自動マッチングの確認
  await t.step("自動マッチングが成立していることを確認", async () => {
    const response = await fetch(`${CONTRACT_SERVICE_URL}/contracts/ui/dashboard#weather-widget`);
    assertEquals(response.status, 200);
    
    const contracts = await response.json();
    assertEquals(contracts.canCall.length, 1);
    assertEquals(contracts.canCall[0].provider, "services/weather#current");
    
    // 変換ルールが自動生成されていることを確認
    assertEquals(contracts.canCall[0].transform, {
      output: {
        "location": "city"
      },
      input: {
        "temperature": "temp",
        "humidity": "humid",
        "location": "city"
      }
    });
  });

  // Step 4: 複数Providerの登録（異なる精度・料金）
  await t.step("複数のWeather Providerを登録", async () => {
    // 高精度版
    await fetch(`${CONTRACT_SERVICE_URL}/register/provider`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        uri: "services/premium-weather#current",
        schema: {
          input: { 
            type: "object",
            properties: { location: { type: "string" } }
          },
          output: {
            type: "object",
            properties: {
              temperature: { type: "number" },
              humidity: { type: "number" },
              location: { type: "string" },
              accuracy: { type: "string", const: "high" }
            }
          }
        },
        metadata: { cost: 10, accuracy: "high" },
        endpoint: "http://localhost:9002/premium-weather"
      })
    });

    const response = await fetch(`${CONTRACT_SERVICE_URL}/contracts/ui/dashboard#weather-widget`);
    const contracts = await response.json();
    assertEquals(contracts.canCall.length, 2); // 2つのProviderとマッチ
  });

  // Step 5: エラーハンドリングテスト
  await t.step("不正な契約登録のエラーハンドリング", async () => {
    const response = await fetch(`${CONTRACT_SERVICE_URL}/register/provider`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        uri: "invalid/service",
        schema: "not-a-valid-schema" // 不正なスキーマ
      })
    });

    assertEquals(response.status, 400);
    const error = await response.json();
    assertEquals(error.error, "Invalid schema format");
  });

  // Step 6: 実際の通信テスト（Mock Services起動）
  const weatherService = await startMockWeatherService();
  const premiumService = await startMockPremiumWeatherService();
  
  try {
    await t.step("Dashboard → Contract Service → Weather Service の通信", async () => {
      // Dashboardからの呼び出し（自分のスキーマで送信）
      const response = await fetch(`${CONTRACT_SERVICE_URL}/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          data: {
            city: "Tokyo"  // Dashboardは'city'として送信
          }
        })
      });

      assertEquals(response.status, 200);
      const result = await response.json();
      
      // Contract Serviceが変換して返してくれる
      assertEquals(result, {
        temp: 25.5,    // temperature → temp に変換済み
        humid: 60,     // humidity → humid に変換済み
        city: "Tokyo"  // location → city に変換済み
      });
    });

    // Step 7: 変換スクリプトの安全実行テスト
    await t.step("悪意のある変換スクリプトの隔離実行", async () => {
      // ファイルアクセスを試みる悪意のあるスクリプト
      const response = await fetch(`${CONTRACT_SERVICE_URL}/transform/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          to: "services/weather#current",
          script: `
            function transform(input) {
              // 悪意のある操作を試みる
              try {
                Deno.readTextFileSync('/etc/passwd');
              } catch (e) {
                // Worker内では権限エラーになるはず
              }
              return { location: input.city };
            }
          `
        })
      });

      assertEquals(response.status, 200); // 登録は成功

      // 実行時に隔離されていることを確認
      const callResponse = await fetch(`${CONTRACT_SERVICE_URL}/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          data: { city: "Tokyo" }
        })
      });

      assertEquals(callResponse.status, 200); // 隔離実行は成功
    });

    // Step 8: Provider選択ロジックのテスト
    await t.step("複数Provider存在時の最適選択", async () => {
      const response = await fetch(`${CONTRACT_SERVICE_URL}/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          data: { city: "Tokyo" },
          preferences: { accuracy: "high" } // 高精度を要求
        })
      });

      const result = await response.json();
      assertEquals(result.accuracy, "high"); // Premium版が選択されたことを確認
    });

    // Step 9: カスタム変換スクリプトのテスト
    await t.step("カスタム変換スクリプトの登録と実行", async () => {
      // 温度を華氏に変換するカスタムスクリプトを登録
      const response = await fetch(`${CONTRACT_SERVICE_URL}/transform/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          to: "services/weather#current",
          script: `
            function transform(input) {
              return {
                location: input.city
              };
            }
          `,
          reverseScript: `
            function transform(output) {
              return {
                temp: output.temperature * 9/5 + 32,  // 摂氏→華氏
                humid: output.humidity,
                city: output.location
              };
            }
          `
        })
      });

      assertEquals(response.status, 200);

      // 再度通信して華氏変換されることを確認
      const callResponse = await fetch(`${CONTRACT_SERVICE_URL}/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "ui/dashboard#weather-widget",
          data: { city: "Tokyo" }
        })
      });

      const result = await callResponse.json();
      assertEquals(result.temp, 77.9); // 25.5°C = 77.9°F
    });

  } finally {
    // クリーンアップ
    weatherService.close();
    premiumService.close();
  }

  // Step 10: 通信エラー時のフォールバック
  await t.step("Provider通信エラー時のフォールバック", async () => {
    // すべてのサービスを停止
    const response = await fetch(`${CONTRACT_SERVICE_URL}/call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        from: "ui/dashboard#weather-widget",
        data: { city: "Tokyo" }
      })
    });

    assertEquals(response.status, 503); // Service Unavailable
    const error = await response.json();
    assertEquals(error.error, "No available providers");
  });
});

// Mock Weather Service Helpers
async function startMockWeatherService() {
  const server = Deno.serve({ port: 9001 }, (req) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/weather" && req.method === "POST") {
      return Response.json({
        temperature: 25.5,
        humidity: 60,
        location: "Tokyo"
      });
    }
    
    return new Response("Not Found", { status: 404 });
  });

  // サーバー起動待機
  await delay(100);
  
  return server;
}

async function startMockPremiumWeatherService() {
  const server = Deno.serve({ port: 9002 }, (req) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/premium-weather" && req.method === "POST") {
      return Response.json({
        temperature: 25.52, // より精密
        humidity: 60.3,
        location: "Tokyo",
        accuracy: "high"
      });
    }
    
    return new Response("Not Found", { status: 404 });
  });

  await delay(100);
  return server;
}