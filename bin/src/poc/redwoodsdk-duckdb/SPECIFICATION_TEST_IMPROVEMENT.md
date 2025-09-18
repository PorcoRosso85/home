# RedwoodSDK-init テスト基盤改善仕様書

## 概要
ボイラープレートとして必要最小限のテスト例とテスト基盤を追加する。

## 目的
- 開発者にテストの書き方を示す
- Cloudflare Workers環境特有のテスト方法を提供
- 品質保証の基盤を確立

## 実装要件

### 1. テスト設定ファイル

#### vitest.config.ts
```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'miniflare',
    setupFiles: ['./tests/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 2. 必須テストファイル

#### tests/setup.ts
- Miniflare環境セットアップ
- モックオブジェクト初期化
- テストヘルパー関数定義

#### tests/auth.test.ts
- WebAuthn認証フローのサンプルテスト
- モック認証の実装例
- エラーケースのテスト例

#### tests/worker.test.ts
- ルーティングテスト
- ミドルウェアテスト
- レスポンス検証例

#### tests/db.test.ts
- D1データベース操作テスト
- マイグレーション検証
- トランザクションテスト例

#### tests/README.md
- テストの実行方法
- 新しいテストの追加方法
- モックの作成方法
- CI/CD統合ガイド

### 3. package.json更新

```json
{
  "scripts": {
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "miniflare": "^3.0.0",
    "@cloudflare/vitest-pool-workers": "^0.1.0"
  }
}
```

### 4. 実装優先順位

1. **Phase 1**: 基本設定（vitest.config.ts, setup.ts）
2. **Phase 2**: 単純なテスト例（worker.test.ts）
3. **Phase 3**: 複雑なテスト例（auth.test.ts, db.test.ts）
4. **Phase 4**: ドキュメント（tests/README.md）

## 成功基準
- `npm test`で最低3つのテストが実行される
- テストカバレッジが測定可能
- 開発者が新しいテストを追加できる

## 非機能要件
- テスト実行時間: 10秒以内
- モック使用でネットワーク依存なし
- CI/CD統合可能な構成

---
*Created by Designer Y - 2025-09-07*