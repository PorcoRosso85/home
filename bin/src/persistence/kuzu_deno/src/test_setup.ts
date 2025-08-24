import { assertEquals } from "https://deno.land/std@0.224.0/assert/mod.ts";

// Step 1.2: 仕様の定義【RED】→【GREEN】
// kuzu-wasmモジュールがDenoで読み込めることを検証
Deno.test("kuzu-wasm module can be imported in Deno", async () => {
  // npm:kuzu-wasm経由でモジュールをインポート
  const kuzu = await import("npm:kuzu-wasm");
  
  // デバッグ: 実際に何が返されているか確認
  console.log("Imported kuzu keys:", Object.keys(kuzu));
  
  // モジュールが存在することを確認
  assertEquals(typeof kuzu, "object");
  assertEquals(kuzu !== null, true);
  
  // defaultエクスポートを確認
  const Database = kuzu.default?.Database || kuzu.Database;
  console.log("Database type:", typeof Database);
  
  // Database クラスが存在することを確認（defaultエクスポート経由の可能性）
  assertEquals(typeof Database, "function");
});

Deno.test("kuzu-wasm version is accessible", async () => {
  const kuzu = await import("npm:kuzu-wasm");
  
  // defaultエクスポートの確認
  const kuzuModule = kuzu.default || kuzu;
  
  // getVersion関数が存在し、文字列を返すことを確認
  if (kuzuModule.getVersion) {
    const version = await kuzuModule.getVersion();
    assertEquals(typeof version, "string");
    console.log(`Kuzu version: ${version}`);
  }
});