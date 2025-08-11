# X API Read実装 - Baby Steps計画

## 前提条件
- Bun/TypeScript環境（`bin/src/flakes/bun`を使用）
- TypeScript/JavaScript SDK（公式提供あり）
- 最小限のREAD実装（タイムライン取得）

## Baby Steps（15-30分単位）

### Step 1: プロジェクト基盤の構築
**所要時間**: 15分

#### 1.1: 価値の明文化（WHY）
- X APIとの接続実証により、SNS統合の技術的可能性を確認
- 最小限の実装でAPIアクセスパターンを確立

#### 1.2: 仕様の定義（WHAT）【RED】
```typescript
// test/setup.spec.ts
test("プロジェクトが正しく初期化される", () => {
  expect(existsSync("package.json")).toBe(true);
  expect(existsSync("tsconfig.json")).toBe(true);
  expect(existsSync(".env.example")).toBe(true);
});
```

#### 1.3: 実現（HOW）【GREEN】
- `bun init`でプロジェクト初期化
- flake.nixの作成（bunフレークを継承）
- `.env.example`の作成

#### 1.4: 検証（CHECK）
- `bun test`で確認

---

### Step 2: X API SDK依存関係の設定
**所要時間**: 15分

#### 2.1: 価値の明文化（WHY）
- 公式SDKを使用することで信頼性の高い実装を実現
- 認証フローの複雑さをSDKに委譲

#### 2.2: 仕様の定義（WHAT）【RED】
```typescript
// test/dependencies.spec.ts
test("X API SDKがインストールされている", async () => {
  const pkg = await import("../package.json");
  expect(pkg.dependencies).toHaveProperty("twitter-api-sdk");
});
```

#### 2.3: 実現（HOW）【GREEN】
- `bun add twitter-api-sdk`でSDK追加
- 型定義の確認

#### 2.4: 検証（CHECK）
- `bun test`で依存関係確認

---

### Step 3: 環境変数による認証情報管理
**所要時間**: 20分

#### 3.1: 価値の明文化（WHY）
- セキュアな認証情報管理の実現
- 環境ごとの設定切り替えを可能に

#### 3.2: 仕様の定義（WHAT）【RED】
```typescript
// test/config.spec.ts
import { getConfig } from "../src/config";

test("環境変数から認証情報を取得できる", () => {
  const config = getConfig();
  expect(config.bearerToken).toBeDefined();
  expect(config.bearerToken).not.toBe("");
});
```

#### 3.3: 実現（HOW）【GREEN】
```typescript
// src/config.ts
export function getConfig() {
  const bearerToken = process.env.X_BEARER_TOKEN;
  if (!bearerToken) {
    throw new Error("X_BEARER_TOKEN is required");
  }
  return { bearerToken };
}
```

#### 3.4: 検証（CHECK）
- `.env.test`を作成してテスト実行

---

### Step 4: APIクライアントの初期化
**所要時間**: 20分

#### 4.1: 価値の明文化（WHY）
- API接続の基盤確立
- 再利用可能なクライアント構造

#### 4.2: 仕様の定義（WHAT）【RED】
```typescript
// test/client.spec.ts
import { createClient } from "../src/client";

test("APIクライアントを初期化できる", () => {
  const client = createClient();
  expect(client).toBeDefined();
  expect(client.tweets).toBeDefined();
});
```

#### 4.3: 実現（HOW）【GREEN】
```typescript
// src/client.ts
import { Client } from "twitter-api-sdk";
import { getConfig } from "./config";

export function createClient() {
  const { bearerToken } = getConfig();
  return new Client(bearerToken);
}
```

#### 4.4: 検証（CHECK）
- `bun test`でクライアント初期化確認

---

### Step 5: 最小限のツイート取得機能
**所要時間**: 30分

#### 5.1: 価値の明文化（WHY）
- READ機能の実証
- APIレスポンス構造の理解

#### 5.2: 仕様の定義（WHAT）【RED】
```typescript
// test/read.spec.ts
import { getTweet } from "../src/read";

test("指定したIDのツイートを取得できる", async () => {
  const tweetId = "1234567890"; // テスト用ID
  const tweet = await getTweet(tweetId);
  expect(tweet).toBeDefined();
  expect(tweet.data).toBeDefined();
  expect(tweet.data.id).toBe(tweetId);
});
```

#### 5.3: 実現（HOW）【GREEN】
```typescript
// src/read.ts
import { createClient } from "./client";

export async function getTweet(id: string) {
  const client = createClient();
  return await client.tweets.findTweetById(id);
}
```

#### 5.4: 検証（CHECK）
- モックを使用したテスト実行
- 実際のAPIでの動作確認（手動）

---

### Step 6: CLIインターフェース
**所要時間**: 20分

#### 6.1: 価値の明文化（WHY）
- ユーザーが簡単にAPI機能を試せる
- POCとしての動作実証

#### 6.2: 仕様の定義（WHAT）【RED】
```typescript
// test/cli.spec.ts
test("CLIコマンドが正しく実行される", async () => {
  const result = await $`bun run src/cli.ts read --id 123`;
  expect(result.exitCode).toBe(0);
});
```

#### 6.3: 実現（HOW）【GREEN】
```typescript
// src/cli.ts
#!/usr/bin/env bun

import { getTweet } from "./read";

const args = process.argv.slice(2);
if (args[0] === "read" && args[1] === "--id") {
  const tweet = await getTweet(args[2]);
  console.log(JSON.stringify(tweet, null, 2));
}
```

#### 6.4: 検証（CHECK）
- `bun run src/cli.ts read --id [実際のツイートID]`

---

## 実装順序と優先度

1. **Step 1-2**: 基盤構築（必須）
2. **Step 3-4**: 認証とクライアント（必須）
3. **Step 5**: READ機能の核心（必須）
4. **Step 6**: ユーザビリティ（オプション）

## 成功基準
- 各Stepが独立して動作確認可能
- テストがすべてGREEN状態
- 環境変数のみで設定可能
- `nix run`で即座に実行可能