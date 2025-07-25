import { R2Adapter } from "../infrastructure.ts";
import { StorageObject } from "../domain.ts";

async function main() {
  // R2アダプターの作成
  const r2 = new R2Adapter({
    endpoint: Deno.env.get("R2_ENDPOINT") || "https://your-account-id.r2.cloudflarestorage.com",
    region: "auto",
    credentials: {
      accessKeyId: Deno.env.get("R2_ACCESS_KEY_ID") || "",
      secretAccessKey: Deno.env.get("R2_SECRET_ACCESS_KEY") || "",
    },
  });

  const bucketName = "test-bucket";
  const key = "test-file.txt";
  const content = "Hello from R2!";

  try {
    // ファイルのアップロード
    console.log("📤 Uploading file...");
    const uploadedObject = await r2.put(
      bucketName,
      key,
      new TextEncoder().encode(content),
      { contentType: "text/plain" }
    );
    console.log("✅ Uploaded:", uploadedObject);

    // ファイル一覧の取得
    console.log("\n📋 Listing files...");
    const files = await r2.list(bucketName, { prefix: "test-" });
    console.log("Files found:", files.length);
    files.forEach((file) => {
      console.log(`  - ${file.key} (${file.size} bytes)`);
    });

    // ファイルのダウンロード
    console.log("\n📥 Downloading file...");
    const downloadedObject = await r2.get(bucketName, key);
    if (downloadedObject?.body) {
      const downloadedContent = new TextDecoder().decode(downloadedObject.body);
      console.log("✅ Downloaded content:", downloadedContent);
    }

    // ファイルの削除
    console.log("\n🗑️  Deleting file...");
    await r2.delete(bucketName, key);
    console.log("✅ File deleted");

    // 削除確認
    console.log("\n🔍 Verifying deletion...");
    const afterDelete = await r2.list(bucketName, { prefix: "test-" });
    console.log("Files remaining:", afterDelete.length);

  } catch (error) {
    console.error("❌ Error occurred:", error);
    if (error instanceof Error) {
      console.error("Error details:", error.message);
    }
  }
}

// 実行
if (import.meta.main) {
  main().catch(console.error);
}