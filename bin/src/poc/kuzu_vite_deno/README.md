# Kuzu-WASM Vite+Deno POC

最小構成のDeno + Vite + kuzu-wasmのPOCです。

## 🎯 特徴

- **パッケージマネージャー不要**: `nodeModulesDir: false`でローカルにnode_modulesを作成しません
- **ESMベース**: 全てESMで直接インポート
- **最小構成**: 必要最小限の設定のみ
- **WASM対応**: kuzu-wasmをブラウザで実行

## 🚀 起動方法

```bash
# ディレクトリに移動
cd /home/nixos/bin/src/poc/kuzu_vite_deno

# 開発サーバー起動
deno task dev

# または直接実行
deno run -A build.ts
```

## 📁 ファイル構成

```
kuzu_vite_deno/
├── deno.json      # Deno設定（依存関係、タスク）
├── build.ts       # Viteサーバー起動スクリプト
├── index.html     # HTMLエントリーポイント
└── main.ts        # kuzu-wasmを使うメインコード
```

## 🎉 機能

1. **KuzuDB初期化**: インメモリデータベースを作成
2. **テーブル作成**: Personテーブルを作成してサンプルデータを挿入
3. **クエリ実行**: Cypherクエリでデータを取得

## 🔧 技術的なポイント

### Viteプラグイン
- `vite-plugin-wasm`: WASMモジュールをESM形式で使用
- `vite-plugin-top-level-await`: トップレベルでのawaitをサポート

### SharedArrayBuffer対応
```typescript
headers: {
  'Cross-Origin-Embedder-Policy': 'require-corp',
  'Cross-Origin-Opener-Policy': 'same-origin'
}
```

### 最適化設定
```typescript
optimizeDeps: {
  exclude: ['kuzu-wasm'], // WASMモジュールを事前バンドルから除外
}
```

## 🧑 クリーンアップ

```bash
# 一時ファイルを削除
deno task clean
```