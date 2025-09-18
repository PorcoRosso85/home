# WASM Integration Guide for Waku + @cloudflare/vite-plugin

## 具体的な使い方

### 1. 基本的なWASMインポート

```typescript
// src/lib/wasm-example.ts
import wasmModule from "./example.wasm";

// WASMモジュールはWebAssembly.Moduleとして自動的に初期化される
export async function useWasm() {
  const instance = await WebAssembly.instantiate(wasmModule);
  return instance.exports;
}
```

### 2. NPMパッケージのWASM使用例（Shiki）

```typescript
// src/lib/syntax-highlighter.ts
import { getHighlighter } from 'shiki';

// ShikiのWASMファイルは@cloudflare/vite-pluginが自動的に処理
export async function createHighlighter() {
  const highlighter = await getHighlighter({
    themes: ['github-dark'],
    langs: ['javascript', 'typescript']
  });
  return highlighter;
}
```

### 3. 設定の詳細

#### waku.config.ts
```typescript
import { defineConfig } from "waku/config";
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineConfig({
  vite: {
    plugins: [
      cloudflare({
        viteEnvironment: { name: "rsc" } // RSC環境でWASMを処理
      }),
    ],
  },
});
```

## ビルドプロセスの動作

### 開発時（npm run dev）
1. `.wasm`ファイルのインポートを検出
2. Module Fallback Serviceを使用してWASMモジュールをロード
3. `WebAssembly.Module`として利用可能に

### ビルド時（npm run build）
1. WASMファイルをアセットとして出力（dist/assets/）
2. インポートパスを自動的に置換
3. Cloudflare Workersで実行可能な形式にバンドル

## NPMパッケージのWASM処理

@cloudflare/vite-pluginは以下を自動処理：

1. **node_modules内のWASMファイル検出**
   - パッケージが`.wasm`ファイルを含む場合、自動的に検出
   
2. **インポートパスの解決**
   ```javascript
   // Before (開発時)
   import wasm from "package-name/lib/module.wasm";
   
   // After (ビルド後)
   // dist/assets/module-[hash].wasmとして出力され、
   // 適切なパスに自動変換
   ```

3. **WebAssembly.Module初期化**
   - Cloudflare Workers環境で正しく動作するよう自動変換

## 実装例：画像処理ライブラリ

```typescript
// src/lib/image-processor.ts
import resvgWasm from "@resvg/resvg-wasm/index_bg.wasm";
import init from "@resvg/resvg-wasm";

let initialized = false;

export async function processImage(svgString: string) {
  if (!initialized) {
    // WASMモジュールを初期化
    await init(resvgWasm);
    initialized = true;
  }
  
  // resvgを使用してSVGをPNGに変換
  const resvg = new Resvg(svgString);
  const pngBuffer = resvg.render().asPng();
  return pngBuffer;
}
```

## トラブルシューティング

### WASMファイルが見つからない場合
- `wrangler.jsonc`の`compatibility_flags`に`nodejs_compat`が含まれているか確認
- ビルド出力の`dist/assets`ディレクトリにWASMファイルが生成されているか確認

### ビルドエラーが発生する場合
- @cloudflare/vite-pluginが`viteEnvironment: { name: "rsc" }`に設定されているか確認
- Viteのバージョンが7.0以上であることを確認

## まとめ

@cloudflare/vite-pluginを使用することで：
- NPMパッケージのWASMファイルが自動的にビルドに含まれる
- 開発時とビルド時の両方で適切に動作
- Cloudflare Workers環境で実行可能な形式に自動変換
- 特別な設定なしでShikiなどのWASM依存パッケージが利用可能