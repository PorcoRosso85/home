# kuzu/browse E2Eテスト

## E2Eテストの意義

E2E（End-to-End）テストは、実際のユーザーの操作をシミュレートし、システム全体の統合動作を確認するテストです。

### 基本原則

1. **UI操作のみ**: Puppeteerを使用してブラウザ経由でUIを操作
2. **バックエンド直接アクセス禁止**: WebSocket、DB、ファイルシステムへの直接接続は行わない
3. **ユーザー視点**: 実際のユーザーが行う操作（クリック、入力、表示確認）のみを実行

### ディレクトリ構成

```
test/e2e/
├── cases/                    # テストケース（Deno.test形式）
│   ├── setup.ts             # 共通セットアップ
│   ├── basic.test.ts        # 基本動作テスト
│   └── mergeConflict.test.ts # merge/conflictフローテスト
├── fixtures/                # テストデータ（必要に応じて）
└── README.md               # このファイル
```

### 実行方法

```bash
# 前提条件
# 1. Viteサーバー起動
cd /home/nixos/bin/src/kuzu/browse
deno task dev

# 2. RPCサーバー起動（UIが依存する場合）
cd /home/nixos/bin/src/rpc
deno run -A main.ts

# 3. E2Eテスト実行
cd /home/nixos/bin/src/kuzu/browse

# すべてのテストを実行（前提条件チェック付き）
deno run -A test/e2e/run.ts

# Denoタスクを使用
deno task test:e2e           # すべてのE2Eテスト
deno task test:e2e:basic     # 基本テストのみ
deno task test:e2e:merge     # merge/conflictテストのみ
deno task test:e2e:watch     # ファイル変更監視モード

# 直接実行
cd test/e2e
deno test -A

# 特定のテストファイルを実行
deno test -A cases/basic.test.ts
deno test -A cases/mergeConflict.test.ts

# パターンでフィルタ
deno test -A --filter "アプリケーション起動"
deno test -A --filter "conflict"

# ブラウザを表示モードで実行
HEADLESS=false deno test -A

# カスタムChromiumパスを指定
CHROMIUM_PATH=/path/to/chromium deno test -A

# 並列実行を無効化（デバッグ時）
deno test -A --jobs 1
```

### 環境変数

- `HEADLESS`: `false`に設定するとブラウザを表示モードで実行
- `CHROMIUM_PATH`: Chromiumの実行パスを指定（デフォルト: `/home/nixos/.nix-profile/bin/chromium`）

### テストの書き方

```typescript
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createBrowser, getBrowserOptions, VITE_URL } from "./setup.ts";

Deno.test("E2E: テスト名", async () => {
  const options = getBrowserOptions();
  const browser = await createBrowser(options);
  
  try {
    const page = await browser.newPage();
    await page.goto(VITE_URL);
    
    // UI操作
    await page.click("[data-testid='button']");
    
    // 結果確認
    const result = await page.$("[data-testid='result']");
    assertExists(result, "結果要素が存在すること");
    
    await page.close();
  } finally {
    await browser.close();
  }
});
```

### 注意事項

- テストケースはUIの実装に合わせて更新する
- セレクタ（data-testid等）は実際のUI実装に合わせる
- モック実装はサーバー側で行う（E2Eテスト側では行わない）
- 各テストは独立して実行可能にする（前のテストの状態に依存しない）
