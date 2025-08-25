# kuzu_bun

Bun環境でKuzuDBとkuzu-wasmを提供するプロジェクト

## 目的

- bunによるkuzu提供, kuzu-wasm提供

## ⚠️ 重要な制約

**kuzu-wasmはNode.jsの`worker_threads`に依存しているため、Bunでは動作しません。**

### 実行環境別サポート状況
- **Node.js**: ✅ 完全サポート（`node test-nodejs.js`で動作確認可能）
- **Bun**: ❌ worker_threads非対応のため実行時エラー（`Cannot find module 'threads/worker'`）
- **Browser**: ✅ 完全サポート

## ディレクトリ構成

```
kuzu_bun/
├── examples/              # 使用例
│   ├── browser_example.html    # ブラウザ環境での基本例
│   ├── browser_in_memory.html  # インメモリDBの例
│   ├── browser_in_memory.js    # インメモリDB実装
│   └── nodejs_example.js       # Node.js環境での例
└── flake.nix             # Nix開発環境定義
```

## 使用方法

### 開発環境の起動

```bash
nix develop
```

### サンプルの実行

#### ブラウザ環境
1. HTTPサーバーを起動
2. `examples/browser_example.html`または`examples/browser_in_memory.html`を開く

#### Node.js/Bun環境
```bash
bun examples/nodejs_example.js
```

## 技術スタック

- **Bun**: JavaScriptランタイム
- **KuzuDB**: 埋め込み型グラフデータベース
- **kuzu-wasm**: KuzuDBのWebAssembly版
- **Nix**: 再現可能な開発環境