/**
 * 基本動作E2Eテスト
 * - ブラウザ経由でUIを操作
 * - 実際のユーザー操作をシミュレート
 * - バックエンドへの直接アクセスは禁止
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import puppeteer from "npm:puppeteer-core@23.1.0";

const VITE_URL = "http://localhost:5173";

type TestSuccess = {
  test: string;
  passed: true;
};

type TestError = {
  test: string;
  passed: false;
  error: string;
};

type TestResult = TestSuccess | TestError;

export async function runBasicTests(browser: any): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const context = await browser.createBrowserContext();
  
  try {
    // アプリケーション起動テスト
    console.log("  - アプリケーション起動テスト開始");
    const appStartResult = await testApplicationStart(context);
    results.push(appStartResult);
    console.log(`    結果: ${appStartResult.passed ? "✅" : "❌"}`);
    
    // UI初期表示テスト
    console.log("  - UI初期表示テスト開始");
    const uiDisplayResult = await testUIDisplay(context);
    results.push(uiDisplayResult);
    console.log(`    結果: ${uiDisplayResult.passed ? "✅" : "❌"}`);
    
    // グラフDB接続状態表示テスト
    console.log("  - グラフDB接続状態表示テスト開始");
    const dbStatusResult = await testGraphDBStatus(context);
    results.push(dbStatusResult);
    console.log(`    結果: ${dbStatusResult.passed ? "✅" : "❌"}`);
    
    // RPC接続状態表示テスト
    console.log("  - RPC接続状態表示テスト開始");
    const rpcStatusResult = await testRPCStatus(context);
    results.push(rpcStatusResult);
    console.log(`    結果: ${rpcStatusResult.passed ? "✅" : "❌"}`);
    
  } finally {
    await context.close();
  }
  
  return results;
}

async function testApplicationStart(context: any): Promise<TestResult> {
  const testName = "アプリケーション起動";
  
  try {
    const page = await context.newPage();
    
    // ページへ移動
    const response = await page.goto(VITE_URL, { 
      waitUntil: "networkidle0",
      timeout: 30000 
    });
    
    if (!response || !response.ok()) {
      return {
        test: testName,
        passed: false,
        error: `HTTPステータス: ${response?.status() || "unknown"}`
      };
    }
    
    // React root要素の確認
    await page.waitForSelector("#root", { timeout: 5000 });
    
    await page.close();
    
    return {
      test: testName,
      passed: true
    };
  } catch (error) {
    return {
      test: testName,
      passed: false,
      error: error.message
    };
  }
}

async function testUIDisplay(context: any): Promise<TestResult> {
  const testName = "UI初期表示";
  
  try {
    const page = await context.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // タイトル確認
    const title = await page.title();
    console.log(`    ページタイトル: "${title}"`);
    
    // TODO: 実際のUI要素を確認
    // 例:
    // - ヘッダー要素
    // - メインコンテンツエリア
    // - ナビゲーション要素
    console.log("    TODO: 実際のUI要素セレクタを実装");
    
    await page.close();
    
    return {
      test: testName,
      passed: true
    };
  } catch (error) {
    return {
      test: testName,
      passed: false,
      error: error.message
    };
  }
}

async function testGraphDBStatus(context: any): Promise<TestResult> {
  const testName = "グラフDB接続状態表示";
  
  try {
    const page = await context.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // UIが完全に読み込まれるまで待機
    await page.waitForTimeout(2000);
    
    // TODO: UI上のDB接続状態表示を確認
    // 例:
    // - 接続ステータスインジケーター
    // - 接続状態テキスト
    // - エラーメッセージの非表示確認
    console.log("    TODO: DB接続状態のUI要素を確認");
    
    await page.close();
    
    return {
      test: testName,
      passed: true
    };
  } catch (error) {
    return {
      test: testName,
      passed: false,
      error: error.message
    };
  }
}

async function testRPCStatus(context: any): Promise<TestResult> {
  const testName = "RPC接続状態表示";
  
  try {
    const page = await context.newPage();
    await page.goto(VITE_URL, { waitUntil: "networkidle0" });
    
    // UIが完全に読み込まれるまで待機
    await page.waitForTimeout(2000);
    
    // TODO: UI上のRPC接続状態表示を確認
    // 例:
    // - RPC接続インジケーター
    // - WebSocket接続状態
    // - エラーメッセージの非表示確認
    console.log("    TODO: RPC接続状態のUI要素を確認");
    
    await page.close();
    
    return {
      test: testName,
      passed: true
    };
  } catch (error) {
    return {
      test: testName,
      passed: false,
      error: error.message
    };
  }
}
