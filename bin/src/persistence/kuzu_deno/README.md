# Deno + Kuzu-wasm Flake

## 責務

このNix flakeは以下の責務を持ちます：

1. **Deno実行環境の提供**
   - 最新のDeno runtimeを提供
   - TypeScript/JavaScript実行環境

2. **Kuzu-wasmパッケージ管理**
   - `npm i kuzu-wasm`によるパッケージインストール
   - WebAssemblyベースのグラフデータベース

3. **ユニバーサル実装**
   - ブラウザ環境での動作対応
   - サーバー環境での動作対応
   - 同一コードベースで両環境をサポート

## セットアップ

```bash
# 開発環境に入る
nix develop

# kuzu-wasmをインストール
npm i kuzu-wasm
```

## 使用方法

### サーバーサイド (Deno)

```typescript
import Database from "kuzu-wasm";

const db = await Database.create();
const conn = await db.connect();

// Cypher クエリの実行
const result = await conn.query("CREATE (n:Person {name: 'Alice'})");
```

### ブラウザサイド

```typescript
// 同じコードがブラウザでも動作
import Database from "kuzu-wasm";

const db = await Database.create();
const conn = await db.connect();

// WebAssemblyが自動的にブラウザ環境で初期化される
const result = await conn.query("MATCH (n) RETURN n");
```

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Nix Flake               │
│  ┌───────────┬────────────┐     │
│  │   Deno    │  Node.js   │     │
│  │  Runtime  │  (for npm) │     │
│  └───────────┴────────────┘     │
│           ↓                      │
│  ┌─────────────────────────┐    │
│  │     kuzu-wasm           │    │
│  │  (WebAssembly module)   │    │
│  └─────────────────────────┘    │
│           ↓                      │
│  ┌──────────┬──────────────┐    │
│  │ Browser  │   Server      │    │
│  │ Runtime  │   Runtime     │    │
│  └──────────┴──────────────┘    │
└─────────────────────────────────┘
```

## 特徴

- **WebAssembly活用**: プラットフォーム非依存の高速実行
- **型安全**: TypeScriptによる型定義サポート
- **グラフDB**: Cypherクエリによる直感的なデータ操作
- **Nix管理**: 再現可能な開発環境

## 開発

```bash
# flake環境でDenoスクリプトを実行
deno run --allow-read --allow-write main.ts

# テスト実行
deno test

# ビルド（ブラウザ向けバンドル）
deno bundle main.ts dist/bundle.js
```

## 依存関係

- Nix Flakes
- Deno (flakeで提供)
- Node.js/npm (kuzu-wasmインストール用)
- kuzu-wasm (npm package)