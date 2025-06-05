#!/usr/bin/env -S deno run -A

/**
 * kuzu/browse E2Eテストランナー
 * 
 * E2Eテストの意義:
 * - 実際のユーザー操作をシミュレート
 * - ブラウザ経由でUIを操作
 * - システム全体の統合動作を確認
 * - バックエンドへの直接アクセスは禁止
 * 
 * CONVENTION準拠: 最小構成、デフォルト引数禁止
 */

import puppeteer from "npm:puppeteer-core@23.1.0";
import { runBasicTests } from "./tests/basicTest.ts";
import { runMergeConflictTests } from "./tests/mergeConflictTest.ts";

const CHROMIUM_PATH = "/home/nixos/.nix-profile/bin/chromium";
const VITE_URL = "http://localhost:5173";

type TestCategory = "basic" | "merge-conflict" | "all";

type TestRunOptions = {
  category: TestCategory;
  headless: boolean;
  chromiumPath: string;
};

async function main() {
  const options = parseArguments();
  
  console.log("🚀 kuzu/browse E2Eテスト開始");
  console.log("📋 テストカテゴリ: " + options.category);
  console.log("🖥️  ヘッドレスモード: " + options.headless);
  console.log("🎯 テスト方針: UI操作のみ（バックエンド直接アクセス禁止）");
  
  // 前提条件の確認
  await checkPrerequisites();
  
  let browser = null;
  
  try {
    // ブラウザ起動
    browser = await puppeteer.launch({
      executablePath: options.chromiumPath,
      headless: options.headless,
      args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    
    console.log("✅ ブラウザ起動成功");
    
    // テスト実行
    const results = await runTests(browser, options.category);
    
    // 結果表示
    displayResults(results);
    
    // 失敗があれば終了コード1
    const hasFailures = results.some(r => !r.passed);
    if (hasFailures) {
      Deno.exit(1);
    }
    
  } catch (error) {
    console.error(`\n❌ エラー: ${error.message}`);
    Deno.exit(1);
  } finally {
    if (browser) {
      await browser.close();
      console.log("🧹 クリーンアップ完了");
    }
  }
}

function parseArguments(): TestRunOptions {
  const args = Deno.args;
  
  // カテゴリ指定
  let category: TestCategory = "all";
  const categoryIndex = args.indexOf("--category");
  if (categoryIndex !== -1 && categoryIndex < args.length - 1) {
    const value = args[categoryIndex + 1];
    if (["basic", "merge-conflict", "all"].includes(value)) {
      category = value as TestCategory;
    }
  }
  
  // ヘッドレスモード
  const headless = !args.includes("--no-headless");
  
  // Chromiumパス
  let chromiumPath = CHROMIUM_PATH;
  const pathIndex = args.indexOf("--chromium-path");
  if (pathIndex !== -1 && pathIndex < args.length - 1) {
    chromiumPath = args[pathIndex + 1];
  }
  
  return { category, headless, chromiumPath };
}

async function checkPrerequisites(): Promise<void> {
  console.log("\n📡 前提条件確認中...");
  
  // Viteサーバー確認
  console.log("  Vite開発サーバー確認中...");
  try {
    const response = await fetch(VITE_URL);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    console.log("  ✅ Vite開発サーバー稼働中");
  } catch {
    console.error("  ❌ Vite開発サーバーが起動していません");
    console.error("\n  起動方法:");
    console.error("    cd /home/nixos/bin/src/kuzu/browse");
    console.error("    deno run -A build.ts");
    Deno.exit(1);
  }
  
  // RPCサーバー確認（UIが依存する場合）
  console.log("  RPCサーバー確認中...");
  try {
    // WebSocketの簡易チェック
    const ws = new WebSocket("ws://localhost:8080");
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        ws.close();
        reject(new Error("timeout"));
      }, 2000);
      
      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve(undefined);
      };
      
      ws.onerror = () => {
        clearTimeout(timeout);
        reject(new Error("connection error"));
      };
    });
    console.log("  ✅ RPCサーバー稼働中");
  } catch {
    console.log("  ⚠️  RPCサーバーが起動していません");
    console.log("     UIがRPCサーバーに依存する場合は起動してください:");
    console.log("     cd /home/nixos/bin/src/rpc && deno run -A main.ts");
    // E2Eテストなので警告のみで続行
  }
  
  console.log("");
}

async function runTests(browser: any, category: TestCategory): Promise<any[]> {
  const allResults = [];
  
  // 基本動作テスト
  if (category === "all" || category === "basic") {
    console.log("📋 基本動作テスト実行中...");
    const results = await runBasicTests(browser);
    allResults.push(...results);
  }
  
  // merge/conflictテスト
  if (category === "all" || category === "merge-conflict") {
    console.log("\n📋 merge/conflictテスト実行中...");
    const results = await runMergeConflictTests(browser);
    allResults.push(...results);
  }
  
  return allResults;
}

function displayResults(results: any[]): void {
  console.log("\n📊 テスト結果:");
  console.log("=".repeat(50));
  
  let passedCount = 0;
  let failedCount = 0;
  
  results.forEach(result => {
    if (result.passed) {
      console.log(`✅ ${result.test}`);
      passedCount++;
    } else {
      console.log(`❌ ${result.test}`);
      console.log(`   エラー: ${result.error}`);
      failedCount++;
    }
  });
  
  console.log("=".repeat(50));
  console.log(`合計: ${results.length} テスト`);
  console.log(`成功: ${passedCount} テスト`);
  console.log(`失敗: ${failedCount} テスト`);
  
  if (failedCount === 0) {
    console.log("\n🎉 すべてのテストが成功しました！");
  } else {
    console.log("\n⚠️  失敗したテストがあります");
  }
}

// ヘルプ表示
function showHelp(): void {
  console.log(`
kuzu/browse E2Eテストランナー

使用方法:
  deno run -A main.ts [オプション]

オプション:
  --category <type>     テストカテゴリを指定
                       basic | merge-conflict | all
                       デフォルト: all
  
  --no-headless        ブラウザを表示モードで実行
  
  --chromium-path <path> Chromiumの実行パスを指定
                        デフォルト: ${CHROMIUM_PATH}
  
  --help               このヘルプを表示

E2Eテストの原則:
  - UI操作のみを実行（クリック、入力、表示確認）
  - バックエンドへの直接アクセスは禁止
  - 実際のユーザー操作をシミュレート

例:
  # すべてのテストを実行
  deno run -A main.ts
  
  # 基本動作テストのみ実行
  deno run -A main.ts --category basic
  
  # ブラウザを表示して実行
  deno run -A main.ts --no-headless
`);
}

if (import.meta.main) {
  if (Deno.args.includes("--help")) {
    showHelp();
    Deno.exit(0);
  }
  
  await main();
}
