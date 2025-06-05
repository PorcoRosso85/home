#!/usr/bin/env -S deno run -A

/**
 * LightPanda + Puppeteer 最小PoC
 * LightPanda公式ドキュメントに従った実装
 */

import puppeteer from "npm:puppeteer-core@23.1.0";

// デバッグモード
const DEBUG = Deno.env.get("DEBUG") === "true";

// メイン処理
async function main() {
  let browser = null;
  
  try {
    // CDP接続（公式ドキュメントの通り）
    console.log("🔌 CDP接続中...");
    browser = await puppeteer.connect({
      browserWSEndpoint: "ws://127.0.0.1:9222",
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
    
    // クリーンアップ（公式例と同じ）
    await page.close();
    await context.close();
    await browser.disconnect();
    
    console.log("\n✅ テスト完了！");
    
  } catch (error) {
    console.error("\n❌ エラーが発生しました");
    console.error(`詳細: ${error.message}`);
    
    if (error.message.includes("Connection refused")) {
      console.error("\n起動方法:");
      console.error("  ./lightpanda serve --host 127.0.0.1 --port 9222");
    }
    
    Deno.exit(1);
  } finally {
    // 接続が残っている場合はクリーンアップ
    if (browser) {
      try {
        await browser.disconnect();
        console.log("🧹 接続クリーンアップ完了");
      } catch {
        // 無視
      }
    }
  }
}

// エントリーポイント
if (import.meta.main) {
  await main();
}