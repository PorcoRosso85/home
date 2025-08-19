# LightPanda Flake

## 目的

このflakeは以下の目的で構成されています：

1. **LightPandaのビルド環境提供**
   - 公式flake対応のLightPandaブラウザのビルド
   - 開発環境の構築

2. **kuzu-wasmのブラウザ動作テスト**
   - KuzuDBのWebAssembly版の動作検証
   - ブラウザ環境でのグラフデータベース機能のテスト

3. **WebWorkerテスト可能性の確認**
   - WebWorker環境でのkuzu-wasm動作検証
   - マルチスレッド処理の実現可能性調査

## 構成ファイル

- `flake.nix`: メインのflake定義（開発環境とビルド設定）
- `flake-prebuilt.nix`: プリビルトバイナリを使用する簡易版
- `flake.lock`: 依存関係のロックファイル

## 使用方法

### 開発環境の起動
```bash
nix develop
```

### LightPandaの実行
```bash
nix run
```

### プリビルト版の使用
```bash
nix develop -f flake-prebuilt.nix
```

## 関連プロジェクト

- [LightPanda](https://github.com/lightpanda-io/browser): JavaScriptランタイム付きヘッドレスブラウザ
- [Kuzu-WASM](https://github.com/kuzudb/kuzu): グラフデータベースのWebAssembly版