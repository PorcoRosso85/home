/**
 * 基本動作E2Eテスト
 * Deno testランナー形式
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createBrowser, checkPrerequisites, getBrowserOptions, VITE_URL } from "./setup.ts";

// テスト前に前提条件確認
await checkPrerequisites();

Deno.test("E2E: アプリケーション起動", async () => {
  const options = getBrowserOptions();
  const browser = await createBrowser(options);
  
  try {
    const page = await browser.newPage();
    
    // ページへ移動
    const response = await page.goto(VITE_URL, { 
      waitUntil: "networkidle0",
      timeout: 30000 
    });
    
    assertExists(response, "レスポンスが存在すること");
    assertEquals(response.ok(), true, "HTTPステータスが正常であること");
    
    // React root要素の確認
    const rootElement = await page.$("#root");
    assertExists(rootElement, "#root要素が存在すること");
    
    await page.close();
  } finally {
    await browser.close();
  }
});

Deno.test("E2E: UI初期表示", async () => {
  const options = getBrowserOptions();
  const browser = await createBrowser(options);
  
  try {
    const page = await browser.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // タイトル確認
    const title = await page.title();
    console.log(`ページタイトル: "${title}"`);
    assertExists(title, "タイトルが存在すること");
    
    // ルート要素の内容確認
    const rootContent = await page.$eval("#root", (el: any) => ({
      hasContent: (el.textContent?.length || 0) > 0,
      childCount: el.children.length
    }));
    
    assertEquals(rootContent.hasContent || rootContent.childCount > 0, true, 
      "ルート要素にコンテンツまたは子要素が存在すること");
    
    // TODO: 実際のUI要素を確認
    // 例:
    // const header = await page.$("header");
    // assertExists(header, "ヘッダー要素が存在すること");
    
    await page.close();
  } finally {
    await browser.close();
  }
});

Deno.test("E2E: グラフDB接続状態表示", async () => {
  const options = getBrowserOptions();
  const browser = await createBrowser(options);
  
  try {
    const page = await browser.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // UIが完全に読み込まれるまで待機
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // ページが正常に読み込まれていることを確認
    const rootContent = await page.$eval("#root", (el: any) => 
      el.textContent?.length || 0
    );
    
    assertEquals(rootContent > 0, true, "ページコンテンツが存在すること");
    
    // TODO: UI上のDB接続状態表示を確認
    // 例:
    // const dbStatus = await page.$("[data-testid='db-status']");
    // assertExists(dbStatus, "DB接続状態要素が存在すること");
    // 
    // const statusText = await page.$eval("[data-testid='db-status']", 
    //   el => el.textContent
    // );
    // assertEquals(statusText?.includes("接続"), true, "接続状態が表示されること");
    
    await page.close();
  } finally {
    await browser.close();
  }
});

Deno.test("E2E: RPC接続状態表示", async () => {
  const options = getBrowserOptions();
  const browser = await createBrowser(options);
  
  try {
    const page = await browser.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // UIが完全に読み込まれるまで待機
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // TODO: UI上のRPC接続状態表示を確認
    // 例:
    // const rpcStatus = await page.$("[data-testid='rpc-status']");
    // assertExists(rpcStatus, "RPC接続状態要素が存在すること");
    // 
    // const statusClass = await page.$eval("[data-testid='rpc-status']",
    //   el => el.className
    // );
    // assertEquals(statusClass.includes("connected") || statusClass.includes("error"), 
    //   true, "接続状態がクラスで表現されること");
    
    console.log("TODO: RPC接続状態のUI要素を確認");
    
    await page.close();
  } finally {
    await browser.close();
  }
});
