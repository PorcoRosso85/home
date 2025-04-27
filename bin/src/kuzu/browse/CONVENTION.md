# Kuzu-Wasm Deno プロジェクト規約

## プロジェクト目的

このプロジェクトは、以下の3つの目標に焦点を当てています：

1. Wasmバイナリを配信する
2. CSVファイルを配信する
3. ブラウザ側でWasmを使ってCSVデータを解析する

## 制約事項

### 許可される変更

- `src` ディレクトリ内のファイルの調整
- `index.html` の修正
- 既存の `build.ts` を利用したViteサーバーの活用

### 禁止される変更

- サーバーサイドのDeno化は行わない

### 不要なファイル

- 重複するJavaScriptファイル（例：`src/lib/kuzu-browser.js`）

## 技術アプローチ

### モジュール管理

- **ESモジュール（ESM）が前提**：CommonJSではなくESMを使用したモジュール管理が必須
- `deno.json`の`imports`セクションに定義されたESMモジュールを使用
- `npm:kuzu-wasm`として直接モジュールをインポート

### ブラウザとの連携

- `index.html`でTypeScriptモジュールを読み込む
- すべてのロジックをTypeScriptモジュールに移動
- `DOMContentLoaded`イベントでアプリケーションを初期化

### CSVファイル

- `public/remote_data.csv`ファイルを活用

## ビルド・実行方法

```bash
# 開発サーバーの実行
deno run -A build.ts

# アクセス
http://localhost:8000/
```

## 注意事項

- このプロジェクトではViteを使用していますが、ViteはESMモジュールの読み込みを行うために使われています
- ESMモジュールとしてkuzu-wasmを読み込むことで、グローバル変数の問題を防止しています
- SharedArrayBufferを利用するために、COOP/COEPヘッダーの設定が必要です（build.tsに設定済み）
- ブラウザでのWasm実行に必要な設定はすでにHTMLのメタタグとViteサーバーの設定に含まれています
