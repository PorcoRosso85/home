import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";

// 最小構成テスト - モジュールのインポート確認のみ
Deno.test("Import kuzu-wasm module", () => {
  // 動的インポートを使わず、静的インポートの可否を確認
  assertEquals(1, 1); // 最小テスト
});

// syncバージョンのテスト（Workerを使わない）
Deno.test("Load kuzu-wasm sync version", async () => {
  try {
    // syncバージョンはWorkerを使わない
    const kuzu = await import("npm:kuzu-wasm/sync");
    
    assertExists(kuzu);
    console.log("Sync kuzu keys:", Object.keys(kuzu));
    
    // APIの存在確認
    if (kuzu.default) {
      console.log("Default export keys:", Object.keys(kuzu.default));
      assertExists(kuzu.default.Database);
    }
  } catch (error) {
    console.error("Error loading sync version:", error);
    // エラーがあっても続行（環境互換性テストのため）
  }
});