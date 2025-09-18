/**
 * URLからのファイルアップロードテスト
 * ローカルファイル（file://）やHTTP URLからのアップロードをテスト
 */

import { createStorageAdapter } from "./mod.ts";

async function testUrlUpload() {
  // 1. ローカルファイルのアップロード (file://)
  console.log("🔍 ローカルファイルのアップロードテスト...");
  
  const localFilePath = "file:///home/nixos/bin/src/storage/s3/README.md";
  
  try {
    // file:// URLからコンテンツを読み込み
    const url = new URL(localFilePath);
    const content = await Deno.readTextFile(url.pathname);
    
    // AWSアダプター（環境変数から設定を読み込む場合）
    const awsAdapter = createStorageAdapter({
      type: "s3",
      endpoint: "https://s3.amazonaws.com",
      region: "us-east-1",
      accessKeyId: Deno.env.get("AWS_ACCESS_KEY_ID") || "test-key",
      secretAccessKey: Deno.env.get("AWS_SECRET_ACCESS_KEY") || "test-secret",
      bucket: Deno.env.get("AWS_S3_BUCKET") || "test-bucket"
    });
    
    // ファイルをアップロード
    const uploadResult = await awsAdapter.upload(
      "uploads/README.md",
      content,
      { contentType: "text/markdown" }
    );
    
    console.log("✅ ローカルファイルアップロード成功:", uploadResult.key);
  } catch (error) {
    console.error("❌ ローカルファイルアップロード失敗:", error);
  }
  
  // 2. HTTPSからの画像アップロード
  console.log("\n🔍 HTTPS URLからの画像アップロードテスト...");
  
  const imageUrl = "https://deno.land/logo.svg";
  
  try {
    // HTTPSから画像を取得
    const response = await fetch(imageUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const imageData = await response.arrayBuffer();
    
    // R2アダプター
    const r2Adapter = createStorageAdapter({
      type: "r2",
      accountId: Deno.env.get("R2_ACCOUNT_ID") || "test-account",
      accessKeyId: Deno.env.get("R2_ACCESS_KEY_ID") || "test-key",
      secretAccessKey: Deno.env.get("R2_SECRET_ACCESS_KEY") || "test-secret",
      bucket: Deno.env.get("R2_BUCKET") || "test-bucket"
    });
    
    // 画像をアップロード
    const uploadResult = await r2Adapter.upload(
      "images/deno-logo.svg",
      new Uint8Array(imageData),
      { contentType: "image/svg+xml" }
    );
    
    console.log("✅ HTTPS画像アップロード成功:", uploadResult.key);
  } catch (error) {
    console.error("❌ HTTPS画像アップロード失敗:", error);
  }
  
  // 3. 実際の使用例
  console.log("\n📝 実際の使用例:");
  console.log(`
// ローカルファイルをAWSにアップロード
const fileUrl = "file:///path/to/local/file.pdf";
const fileContent = await Deno.readFile(new URL(fileUrl).pathname);
await awsAdapter.upload("documents/file.pdf", fileContent, {
  contentType: "application/pdf"
});

// Web画像をR2にアップロード
const imageResponse = await fetch("https://example.com/image.jpg");
const imageBuffer = await imageResponse.arrayBuffer();
await r2Adapter.upload("photos/image.jpg", new Uint8Array(imageBuffer), {
  contentType: "image/jpeg"
});
  `);
}

// メモリ内アダプターでのデモ
async function demoWithInMemory() {
  console.log("\n🎯 メモリ内アダプターでのデモ実行...");
  
  const adapter = createStorageAdapter({ type: "in-memory" });
  
  // ローカルファイルの読み込みとアップロード
  const testFilePath = "./mod.ts";
  const content = await Deno.readTextFile(testFilePath);
  
  await adapter.upload("test/mod.ts", content, {
    contentType: "text/typescript"
  });
  
  // Web画像のダウンロードとアップロード（小さいサンプル画像）
  const response = await fetch("https://via.placeholder.com/150");
  const imageData = await response.arrayBuffer();
  
  await adapter.upload("test/placeholder.png", new Uint8Array(imageData), {
    contentType: "image/png"
  });
  
  // アップロードしたファイルの確認
  const files = await adapter.list({ prefix: "test/" });
  console.log("📁 アップロードされたファイル:");
  for (const file of files.objects) {
    console.log(`  - ${file.key} (${file.size} bytes)`);
  }
}

// デモのみ実行（実際のS3接続はスキップ）
async function runDemo() {
  console.log("\n🎯 ローカルデモ実行（メモリ内アダプター使用）...");
  
  const adapter = createStorageAdapter({ type: "in-memory" });
  
  // 1. ローカルファイルのシミュレーション
  console.log("\n📁 ローカルファイル (file://) のアップロード例:");
  const localContent = "# Sample README\nThis is a test file.";
  await adapter.upload("documents/README.md", localContent, {
    contentType: "text/markdown"
  });
  console.log("✅ file:///path/to/README.md → documents/README.md");
  
  // 2. Web画像のシミュレーション
  console.log("\n🖼️ Web画像 (https://) のアップロード例:");
  const fakeImageData = new Uint8Array([0x89, 0x50, 0x4E, 0x47]); // PNG header
  await adapter.upload("images/logo.png", fakeImageData, {
    contentType: "image/png"
  });
  console.log("✅ https://example.com/logo.png → images/logo.png");
  
  // 3. アップロードしたファイルの確認
  console.log("\n📋 アップロードされたファイル一覧:");
  const allFiles = await adapter.list();
  for (const file of allFiles.objects) {
    const info = await adapter.info(file.key);
    console.log(`  - ${file.key} (${file.size} bytes, ${info.contentType || 'unknown type'})`);
  }
  
  console.log("\n✨ デモ完了！");
}

// 実行
if (import.meta.main) {
  await runDemo();
}