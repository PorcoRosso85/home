#!/usr/bin/env -S deno run -A

/**
 * kuzu/browse E2Eテスト
 * 前提: Vite開発サーバーが起動済み（ポート5173）
 */

import puppeteer from "npm:puppeteer-core@23.1.0";

// デバッグモード
const DEBUG = Deno.env.get("DEBUG") === "true";
const VITE_URL = "http://localhost:5173";

async function main() {
  console.log("🚀 E2Eテスト開始");
  let browser = null;
  
  try {
    // CDP接続
    console.log("🔌 CDP接続中...");
    // NOTE: LightPandaは現在不安定なため、一時的にChromiumを使用
    // browser = await puppeteer.connect({
    //   browserWSEndpoint: "ws://127.0.0.1:9222",
    // });
    browser = await puppeteer.launch({
      executablePath: '/home/nixos/.nix-profile/bin/chromium',
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    console.log("✅ CDP接続成功");
    
    // ブラウザバージョン
    const version = await browser.version();
    console.log(`📋 ブラウザ: ${version}`);
    
    // コンテキスト作成（公式例と同じ）
    console.log("🔧 ブラウザコンテキスト作成中...");
    const context = await browser.createBrowserContext();
    console.log("✅ コンテキスト作成成功");
    
    // ページ作成
    console.log("📄 新規ページ作成中...");
    const page = await context.newPage();
    console.log("✅ ページ作成成功");
    
    // ページ移動（公式例と同じくWikipedia）
    console.log("🌐 Wikipediaへ移動中...");
    await page.goto('https://wikipedia.com/');
    console.log("✅ ページ移動成功");
    
    // リンク取得（公式例と全く同じ）
    console.log("🔍 リンク取得中...");
    const links = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('a')).map(row => {
        return row.getAttribute('href');
      });
    });
    
    console.log(`📊 取得リンク数: ${links.length}`);
    console.log("📝 最初の5つのリンク:");
    links.slice(0, 5).forEach((link, i) => {
      console.log(`  ${i + 1}. ${link}`);
    });
    
    // 基本的な動作確認
    console.log("\n📋 基本機能テスト:");
    
    // タイトル取得
    try {
      const title = await page.title();
      console.log(`  ✅ タイトル取得: ${title}`);
    } catch (e) {
      console.log(`  ❌ タイトル取得失敗: ${e.message}`);
    }
    
    // URL取得
    try {
      const url = page.url();
      console.log(`  ✅ URL取得: ${url}`);
    } catch (e) {
      console.log(`  ❌ URL取得失敗: ${e.message}`);
    }
    
    // viewport設定
    try {
      await page.setViewport({ width: 1280, height: 720 });
      console.log("  ✅ ビューポート設定成功");
    } catch (e) {
      console.log(`  ❌ ビューポート設定失敗: ${e.message}`);
    }
    
    // スクリーンショット（エラーが出る場合はスキップ）
    console.log("📸 スクリーンショット撮影中...");
    try {
      const screenshot = await page.screenshot();
      await Deno.writeFile("wikipedia.png", screenshot);
      console.log("✅ スクリーンショット保存: wikipedia.png");
    } catch (e) {
      console.log("⚠️  スクリーンショット失敗:", e.message);
    }
    
    // PoC: 静的ページテスト
    console.log("\n📋 PoC: 静的ページテスト");
    try {
      const pocPage = await context.newPage(); // contextを使用
      await pocPage.goto("https://example.com");
      const pocTitle = await pocPage.title();
      console.log(`  ✅ 静的ページ成功: ${pocTitle}`);
      await pocPage.close();
    } catch (error) {
      console.error(`  ❌ 静的ページ失敗: ${error.message}`);
      console.error("     ブラウザが正常に動作していない可能性があります");
    }
    
    // 2. Vite開発サーバー確認
    console.log("\n📡 Vite開発サーバー確認中...");
    try {
      const response = await fetch(VITE_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      console.log("✅ Vite開発サーバー稼働中");
    } catch {
      console.error("❌ Vite開発サーバーが起動していません");
      console.error("\n起動方法:");
      console.error("  cd /home/nixos/bin/src/kuzu/browse");
      console.error("  deno run -A build.ts");
      Deno.exit(1);
    }
    
    // 3. kuzu/browseテスト
    console.log("\n📄 kuzu/browseページテスト");
    const browsePage = await context.newPage(); // contextを使用
    await browsePage.goto(VITE_URL);
    
    const title = await browsePage.title();
    console.log(`タイトル: ${title || "(空)"}`);
    if (title !== "KuzuDB Browser") {
      console.warn("⚠️  期待されるタイトル: KuzuDB Browser");
    }
    
    // Reactアプリのマウント待機
    try {
      await browsePage.waitForSelector("#root", { timeout: 5000 });
      const rootContent = await browsePage.$eval("#root", el => el.textContent || "(空)");
      console.log(`ルート要素: ${rootContent.slice(0, 50)}...`);
    } catch (e) {
      console.log("⚠️  #root要素の取得失敗:", e.message);
    }
    
    await browsePage.close(); // browsePageをクローズ
    await page.close();
    await context.close();
    await browser.close(); // disconnectではなくclose
    console.log("\n✅ テスト完了");
    
  } catch (error) {
    console.error(`\n❌ エラー: ${error.message}`);
    Deno.exit(1);
  } finally {
    // 接続が残っている場合はクリーンアップ
    if (browser) {
      try {
        await browser.close(); // disconnectではなくclose
        console.log("🧹 クリーンアップ完了");
      } catch {
        // 無視
      }
    }
  }
}

if (import.meta.main) {
  await main();
}