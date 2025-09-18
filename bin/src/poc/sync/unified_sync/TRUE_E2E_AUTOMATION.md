# 真のE2E自動化実装案

## 前提：完全なエンドツーエンドテストの実現

E2Eテストの定義：
- 実際のWebSocketサーバー
- 実際のブラウザ環境
- 実際のKuzuDB WASM
- 実際のネットワーク通信

## 案A: Nix Flakeによる完全自動化

### flake.nixの拡張

```nix
{
  # 現在の定義に追加
  apps.x86_64-linux = {
    # E2Eテスト実行コマンド
    e2e-test = {
      type = "app";
      program = "${pkgs.writeShellScriptBin "e2e-test" ''
        # プロセス管理用の関数
        cleanup() {
          echo "Cleaning up..."
          kill $WS_PID $HTTP_PID 2>/dev/null || true
        }
        trap cleanup EXIT

        # WebSocketサーバー起動
        echo "Starting WebSocket server..."
        ${pkgs.deno}/bin/deno run --allow-net websocket-server.ts &
        WS_PID=$!
        
        # HTTPサーバー起動
        echo "Starting HTTP server..."
        ${pkgs.deno}/bin/deno run --allow-net --allow-read serve.ts &
        HTTP_PID=$!
        
        # サーバー起動待機
        sleep 3
        
        # Playwrightテスト実行
        echo "Running E2E tests..."
        ${pkgs.nodejs}/bin/npx playwright test \
          --config=playwright.config.ts \
          --reporter=list \
          e2e/test-multi-browser-sync.spec.ts
        
        TEST_RESULT=$?
        
        # 結果を返す
        exit $TEST_RESULT
      ''}/bin/e2e-test";
    };
  };
  
  # 開発シェルの拡張
  devShells.x86_64-linux.default = pkgs.mkShell {
    # ... 既存の設定 ...
    
    shellHook = ''
      # E2Eテストのエイリアス
      alias e2e="nix run .#e2e-test"
      alias e2e-headed="npx playwright test --headed"
      alias e2e-debug="npx playwright test --debug"
      
      echo "🧪 E2E Test Commands:"
      echo "  e2e          - Run headless E2E tests"
      echo "  e2e-headed   - Run E2E tests with browser UI"
      echo "  e2e-debug    - Debug E2E tests interactively"
    '';
  };
}
```

### 実行方法

```bash
# 完全自動E2Eテスト
nix run .#e2e-test

# または開発環境内で
nix develop
e2e
```

## 案B: Playwright Test Fixturesによる完全管理

### サーバー管理をPlaywrightに統合

```typescript
// e2e/fixtures.ts
import { test as base, expect } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';

type TestFixtures = {
  servers: {
    wsServer: ChildProcess;
    httpServer: ChildProcess;
    cleanup: () => void;
  };
};

export const test = base.extend<TestFixtures>({
  servers: async ({}, use) => {
    // WebSocketサーバー起動
    const wsServer = spawn('deno', [
      'run', '--allow-net', 'websocket-server.ts'
    ], { 
      cwd: process.cwd(),
      stdio: 'pipe'
    });
    
    // HTTPサーバー起動
    const httpServer = spawn('deno', [
      'run', '--allow-net', '--allow-read', 'serve.ts'
    ], {
      cwd: process.cwd(),
      stdio: 'pipe'
    });
    
    // ログ出力
    wsServer.stdout.on('data', data => 
      console.log('[WS]', data.toString().trim())
    );
    httpServer.stdout.on('data', data => 
      console.log('[HTTP]', data.toString().trim())
    );
    
    // サーバー起動待機
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // ポート確認
    await waitForPort(8080, 10000);
    await waitForPort(3000, 10000);
    
    // テストで使用
    await use({
      wsServer,
      httpServer,
      cleanup: () => {
        wsServer.kill();
        httpServer.kill();
      }
    });
    
    // 自動クリーンアップ
    wsServer.kill();
    httpServer.kill();
  },
});

// ポート待機ヘルパー
async function waitForPort(port: number, timeout: number) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      const response = await fetch(`http://localhost:${port}`);
      if (response.ok || response.status === 501) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Port ${port} did not become available`);
}
```

### テストの実装

```typescript
// e2e/test-complete-sync.spec.ts
import { test, expect } from './fixtures';

test('完全E2E: 複数ブラウザ同期', async ({ browser, servers }) => {
  // serversフィクスチャでサーバーは自動起動済み
  
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();
  
  const page1 = await context1.newPage();
  const page2 = await context2.newPage();
  
  // 実際のテスト実行
  await page1.goto('http://localhost:3000/demo.html');
  await page2.goto('http://localhost:3000/demo.html');
  
  // KuzuDB WASM初期化待機
  await Promise.all([
    page1.waitForFunction(() => 
      document.getElementById('log')?.textContent?.includes('KuzuDB initialized')
    ),
    page2.waitForFunction(() => 
      document.getElementById('log')?.textContent?.includes('KuzuDB initialized')
    )
  ]);
  
  // Browser1でユーザー作成
  await page1.fill('#userName', 'E2E Test User');
  await page1.click('#createCustom');
  
  // Browser2で同期確認
  await page2.waitForFunction(() => {
    const users = document.getElementById('users')?.textContent || '';
    return users.includes('E2E Test User');
  });
  
  // データ一致を検証
  const users1 = await page1.$$eval('#users .user', els => 
    els.map(el => el.textContent)
  );
  const users2 = await page2.$$eval('#users .user', els => 
    els.map(el => el.textContent)
  );
  
  expect(users1).toEqual(users2);
});
```

## 案C: GitHub Actions統合（CI/CD）

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: cachix/install-nix-action@v22
        with:
          nix_path: nixpkgs=channel:nixos-unstable
      
      - uses: cachix/cachix-action@v12
        with:
          name: mycache
          authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'
      
      - name: Run E2E tests
        run: |
          nix develop --command bash -c "
            # サーバー起動
            deno run --allow-net websocket-server.ts &
            deno run --allow-net --allow-read serve.ts &
            
            # 待機
            sleep 5
            
            # テスト実行
            npx playwright test --reporter=github
          "
```

## 推奨：案Bの実装

### 理由

1. **完全なE2E**: サーバー起動からブラウザ操作まで全自動
2. **Playwrightネイティブ**: フレームワークの機能を最大活用
3. **デバッグ容易**: `--debug`や`--headed`オプションで確認可能
4. **CI/CD対応**: GitHub Actionsで簡単に実行可能

### 実装手順

1. fixturesファイルを作成
2. 既存のテストをfixtures使用に更新
3. playwright.config.tsを簡潔に
4. nix develop環境で実行確認

これにより、完全なE2Eテストの自動化が実現します。