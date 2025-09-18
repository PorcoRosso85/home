# 最も確実なE2Eテスト実装方法

## 各アプローチの確実性評価

### 1. Bashスクリプト方式
```nix
"deno run ws-server.ts & deno run http-server.ts & sleep 3 && playwright test"
```
- ✅ シンプル
- ❌ エラーハンドリングが弱い
- ❌ プロセス管理が原始的
- **確実性: 60%**

### 2. プロセスマネージャー方式（honcho/hivemind）
```nix
"${pkgs.hivemind}/bin/hivemind --print-timestamps Procfile"
```
- ✅ ログ管理が優秀
- ✅ プロセス監視
- ❌ 起動順序の制御が難しい
- **確実性: 75%**

### 3. Nix + systemd方式
```nix
systemd.services = {
  websocket-server = { ... };
  http-server = { after = ["websocket-server.service"]; ... };
  e2e-test = { after = ["http-server.service"]; ... };
};
```
- ✅ 依存関係を明確に定義
- ✅ 再起動ポリシー
- ❌ 開発環境では複雑
- **確実性: 85%**

### 4. Playwright Fixtures + Nix方式（推奨）
```nix
# flake.nix
devShells.x86_64-linux.default = pkgs.mkShell {
  buildInputs = with pkgs; [
    deno
    nodejs
    chromium
    # サーバーヘルスチェック用
    curl
    netcat
  ];
};
```

```typescript
// e2e/test-fixtures.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  servers: async ({}, use) => {
    // Nixが提供する環境で確実に起動
    const servers = await startServersWithHealthCheck();
    await use(servers);
    await servers.cleanup();
  },
});

async function startServersWithHealthCheck() {
  // WebSocketサーバー起動
  const wsServer = spawn('deno', ['run', '--allow-net', 'websocket-server.ts']);
  
  // HTTPサーバー起動
  const httpServer = spawn('deno', ['run', '--allow-net', '--allow-read', 'serve.ts']);
  
  // ヘルスチェック（確実性の核心）
  await waitForHealthy('ws://localhost:8080', {
    timeout: 30000,
    interval: 500,
    healthCheck: async (url) => {
      const ws = new WebSocket(url);
      return new Promise((resolve) => {
        ws.onopen = () => { ws.close(); resolve(true); };
        ws.onerror = () => resolve(false);
      });
    }
  });
  
  await waitForHealthy('http://localhost:3000/demo.html', {
    timeout: 30000,
    interval: 500,
    healthCheck: async (url) => {
      try {
        const res = await fetch(url);
        return res.ok;
      } catch {
        return false;
      }
    }
  });
  
  return {
    wsServer,
    httpServer,
    cleanup: () => {
      wsServer.kill('SIGTERM');
      httpServer.kill('SIGTERM');
    }
  };
}
```

- ✅ ヘルスチェックで確実な起動確認
- ✅ タイムアウトとリトライ
- ✅ 適切なクリーンアップ
- ✅ デバッグが容易
- **確実性: 95%**

## 最終推奨構成

### flake.nix
```nix
{
  devShells.x86_64-linux.default = pkgs.mkShell {
    buildInputs = with pkgs; [
      deno
      nodejs_20
      playwright-driver.browsers
    ];
    
    shellHook = ''
      # Playwright用の環境変数
      export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
      export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
      
      # E2Eテストコマンド
      e2e() {
        echo "🧪 Running E2E tests..."
        npx playwright test "$@"
      }
      
      e2e-ui() {
        echo "🎭 Running E2E tests with UI..."
        npx playwright test --ui "$@"
      }
      
      e2e-debug() {
        echo "🐛 Debugging E2E tests..."
        npx playwright test --debug "$@"
      }
    '';
  };
}
```

### playwright.config.ts
```typescript
export default defineConfig({
  use: {
    // トレース記録（デバッグ用）
    trace: 'on-first-retry',
    // スクリーンショット（失敗時）
    screenshot: 'only-on-failure',
    // ビデオ録画（失敗時）
    video: 'retain-on-failure',
  },
  
  // リトライ設定（確実性向上）
  retries: process.env.CI ? 2 : 0,
  
  // タイムアウト設定
  timeout: 60000,
  
  // レポーター
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/html' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
});
```

### 実行コマンド
```bash
# 開発時（高速）
nix develop -c e2e

# デバッグ時（UI付き）
nix develop -c e2e-ui

# CI/CD（完全自動）
nix develop -c npx playwright test --reporter=github
```

## なぜこれが最も確実か

1. **ヘルスチェック**: サーバーの準備完了を確実に検証
2. **Nix環境**: 依存関係の完全な制御
3. **Playwrightの機能活用**: リトライ、トレース、録画
4. **段階的デバッグ**: UI mode → Debug mode → Trace viewer
5. **CI/CD対応**: GitHub Actions等でそのまま実行可能

この方式なら、ローカルでもCIでも**95%以上の確実性**でE2Eテストを実行できます。