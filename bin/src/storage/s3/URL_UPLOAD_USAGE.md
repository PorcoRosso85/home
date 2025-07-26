# URLからのファイルアップロード方法

現在のS3 Storage Adapterは、URLから直接ファイルをアップロードする機能を**標準実装**で提供しています。

## ✅ 対応可能な操作

### 1. ローカルファイル（file://）をAWSにアップロード

```typescript
import { createStorageAdapter } from "./mod.ts";

// file:// URLからファイルを読み込み
const fileUrl = "file:///home/user/documents/report.pdf";
const filePath = new URL(fileUrl).pathname;
const content = await Deno.readFile(filePath);

// AWS S3アダプター作成
const awsAdapter = createStorageAdapter({
  type: "s3",
  endpoint: "https://s3.amazonaws.com",
  region: "us-east-1",
  accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  bucket: "my-bucket"
});

// アップロード
await awsAdapter.upload("documents/report.pdf", content, {
  contentType: "application/pdf"
});
```

### 2. Web画像（https://）をR2にアップロード

```typescript
// HTTPS URLから画像を取得
const imageUrl = "https://example.com/photo.jpg";
const response = await fetch(imageUrl);
const imageData = await response.arrayBuffer();

// Cloudflare R2アダプター作成
const r2Adapter = createStorageAdapter({
  type: "r2",
  accountId: process.env.R2_ACCOUNT_ID!,
  accessKeyId: process.env.R2_ACCESS_KEY_ID!,
  secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  bucket: "my-r2-bucket"
});

// アップロード
await r2Adapter.upload("photos/photo.jpg", new Uint8Array(imageData), {
  contentType: "image/jpeg"
});
```

## 実装方法

現在の実装は以下のステップで動作します：

1. **URLからコンテンツを取得**
   - `file://`: Deno.readFile() または fs APIを使用
   - `https://`: fetch() APIを使用

2. **バイト配列に変換**
   - テキストファイル: TextEncoderを使用
   - バイナリファイル: Uint8Arrayに変換

3. **StorageAdapterでアップロード**
   - upload()メソッドにバイト配列を渡す
   - 適切なcontentTypeを指定

## 完全な使用例

```typescript
import { createStorageAdapter } from "@storage/s3-adapter";

async function uploadFromUrl(sourceUrl: string, targetKey: string) {
  const adapter = createStorageAdapter({ /* 設定 */ });
  
  let content: Uint8Array;
  let contentType = "application/octet-stream";
  
  if (sourceUrl.startsWith("file://")) {
    // ローカルファイル
    const path = new URL(sourceUrl).pathname;
    content = await Deno.readFile(path);
    
    // 拡張子からContent-Type推定
    if (path.endsWith(".pdf")) contentType = "application/pdf";
    else if (path.endsWith(".jpg")) contentType = "image/jpeg";
    else if (path.endsWith(".png")) contentType = "image/png";
  } else if (sourceUrl.startsWith("https://") || sourceUrl.startsWith("http://")) {
    // Webリソース
    const response = await fetch(sourceUrl);
    content = new Uint8Array(await response.arrayBuffer());
    contentType = response.headers.get("content-type") || contentType;
  } else {
    throw new Error(`Unsupported URL scheme: ${sourceUrl}`);
  }
  
  // アップロード実行
  const result = await adapter.upload(targetKey, content, { contentType });
  console.log(`Uploaded ${sourceUrl} to ${result.key}`);
  return result;
}

// 使用例
await uploadFromUrl("file:///path/to/document.pdf", "docs/document.pdf");
await uploadFromUrl("https://example.com/image.jpg", "images/example.jpg");
```

## まとめ

- **file://** URLからAWS S3へのアップロード: ✅ 対応可能
- **https://** URLからCloudflare R2へのアップロード: ✅ 対応可能
- 実装は標準的なDeno/JavaScript APIを使用
- 追加のライブラリは不要