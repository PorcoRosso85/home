# kuzu_node

Node.js環境でKuzuDBとkuzu-wasmを提供するプロジェクト

## 目的

- Node.jsによるkuzu提供, kuzu-wasm提供

## 動作環境

- **Node.js**: ✅ 完全サポート
- **Bun**: ❌ 非対応（worker_threads依存のため）
- **Browser**: ✅ 完全サポート（ブラウザ向けビルド使用時）

## ディレクトリ構成

```
kuzu_node/
├── infrastructure.ts  # 環境別ローダー
├── domain.ts         # KuzuDB操作ロジック（純粋関数）
├── application.ts    # ユースケース実装
├── mod.ts           # パブリックAPI
├── main.ts          # CLIエントリーポイント
├── test-nodejs.js   # Node.js動作確認スクリプト
├── test-mod.ts      # ライブラリインターフェーステスト
├── package.json     # Node.js依存関係
├── tsconfig.json    # TypeScript設定
└── flake.nix       # Nix開発環境定義
```

## 使用方法

### 開発環境の起動

```bash
nix develop
```

### Node.jsでの動作確認

```bash
node test-nodejs.js
```

### TypeScriptモジュールのテスト

```bash
npx tsx test-mod.ts
```

### ライブラリとしての使用

```typescript
import { loadKuzu, createDatabase, createConnection, executeQuery } from './mod';

async function example() {
  const kuzu = await loadKuzu();
  const db = createDatabase(kuzu);
  const conn = createConnection(kuzu, db);
  
  await executeQuery(conn, "CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))");
  await executeQuery(conn, "CREATE (:Test {id: 1})");
  const results = await executeQuery(conn, "MATCH (t:Test) RETURN t.id");
  
  console.log(results);
  
  await conn.close();
  await db.close();
  await kuzu.close();
}
```

## アーキテクチャ

module_design.md規約に従った3層アーキテクチャ：

1. **Infrastructure層** (`infrastructure.ts`)
   - 環境依存の処理（Node.js/ブラウザ判定）
   - kuzu-wasmモジュールのロード

2. **Domain層** (`domain.ts`)
   - KuzuDB操作の純粋関数
   - 型定義
   - ビジネスロジック

3. **Application層** (`application.ts`)
   - ユースケース実装
   - Infrastructure層とDomain層の統合

## テスト

### テストランナー移行（Node.js → Vitest）

**問題**: Node.jsの組み込みテストランナーでは以下の制限がありました：
- ES modulesとCommonJSの混在で設定が複雑
- kuzu-wasmの動的インポート処理でエラー発生
- TypeScript直接実行における型チェック問題

**解決策**: Vitestに移行することで：
- ES modules完全サポート
- WebAssembly動的インポートの安定動作
- TypeScript統合とVite生態系の活用

### テスト実行

```bash
# Vitestでのテスト実行（単発）
npm test

# Vitestでのテスト実行（監視モード）
npm run test:watch

# カバレッジ付きテスト
npm run test:coverage

# 型チェック
npm run typecheck
```

## 技術スタック

- **Node.js**: JavaScriptランタイム
- **TypeScript**: 型安全な開発
- **Vitest**: モダンテストランナー（ES modules + WebAssembly対応）
- **KuzuDB**: 埋め込み型グラフデータベース
- **kuzu-wasm**: KuzuDBのWebAssembly版
- **Nix**: 再現可能な開発環境