# WASM使用規約

## KuzuDB WASM

### バリアント選択基準
1. **ブラウザ環境（単一スレッド）**: デフォルトビルドを使用
   - 最小サイズ、最高互換性
   - Cross-Origin Isolation不要
   - `import kuzu from "kuzu-wasm"`

2. **ブラウザ環境（マルチスレッド）**: multithreadedビルドを使用
   - パフォーマンス優先
   - Cross-Origin Isolation必要
   - `import kuzu from "kuzu-wasm/multithreaded"`

3. **Node.js環境**: nodejsビルドを使用
   - Node.jsファイルシステム使用
   - CommonJSモジュール
   - `const kuzu = require("kuzu-wasm/nodejs")`

### 非同期/同期選択基準
1. **GUI/Webアプリケーション**: 非同期版（デフォルト）
   - メインスレッドをブロックしない
   - Promiseベース
   - Worker使用

2. **CLI/スクリプト**: 同期版
   - シンプルなAPI
   - プロトタイピング向け
   - `import kuzu from "kuzu-wasm/sync"`

### Worker設定
```typescript
// ブラウザ環境でWorkerパスを設定
import kuzu from "kuzu-wasm";
kuzu.setWorkerPath('/assets/kuzu-worker.js');

// 初期化前に必ず設定
await kuzu.init();
```

### 注意事項
- バリアント間でのオブジェクト共有禁止
- 非同期版と同期版の混在禁止
- Worker設定は初期化前のみ可能