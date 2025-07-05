/**
 * E2E Test Fixtures with Health Checks
 * サーバー管理とヘルスチェックを含むテストフィクスチャ
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - モックフリー実装
 * - 確実なE2E実行
 */

import { test as base } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

type TestFixtures = {
  servers: {
    wsServer: ChildProcess;
    httpServer: ChildProcess;
    cleanup: () => void;
  };
};

export const test = base.extend<TestFixtures>({
  servers: async ({}, use) => {
    const servers = await startServersWithHealthCheck();
    await use(servers);
    await servers.cleanup();
  },
});

export { expect } from '@playwright/test';

// ========== サーバー起動とヘルスチェック ==========

// ポートが使用可能かチェック
async function isPortAvailable(port: number): Promise<boolean> {
  try {
    const response = await fetch(`http://localhost:${port}`, {
      method: 'HEAD',
      signal: AbortSignal.timeout(100)
    });
    return false; // レスポンスがあれば使用中
  } catch {
    return true; // エラーなら利用可能
  }
}

async function startServersWithHealthCheck() {
  console.log('🚀 Starting servers...');
  
  // ポートが使用可能かチェック
  const wsPortAvailable = await isPortAvailable(8080);
  const httpPortAvailable = await isPortAvailable(3000);
  
  if (!wsPortAvailable || !httpPortAvailable) {
    console.log('⚠️  Ports already in use, attempting to use existing servers...');
    // 既存のサーバーが動作しているか確認
    try {
      await waitForHealthy('ws://localhost:8080', {
        timeout: 5000,
        interval: 100,
        name: 'WebSocket Server',
        healthCheck: async (url) => {
          try {
            const ws = new WebSocket(url);
            return new Promise<boolean>((resolve) => {
              ws.onopen = () => {
                ws.close();
                resolve(true);
              };
              ws.onerror = () => resolve(false);
              setTimeout(() => resolve(false), 1000);
            });
          } catch {
            return false;
          }
        }
      });
      
      await waitForHealthy('http://localhost:3000', {
        timeout: 5000,
        interval: 100,
        name: 'HTTP Server',
        healthCheck: async (url) => {
          try {
            const res = await fetch(url);
            return res.ok || res.status === 200;
          } catch {
            return false;
          }
        }
      });
      console.log('✅ Using existing servers');
      return {
        wsServer: null,
        httpServer: null,
        cleanup: () => {} // 既存サーバーはクリーンアップしない
      };
    } catch (e) {
      throw new Error('Ports are in use but servers are not responding');
    }
  }
  
  // WebSocketサーバー起動
  const wsServer = spawn('deno', [
    'run', '--allow-net', '../websocket-server.ts'
  ], {
    cwd: __dirname,
    stdio: 'pipe'
  });
  
  // HTTPサーバー起動
  const httpServer = spawn('deno', [
    'run', '--allow-net', '--allow-read', '../serve.ts'
  ], {
    cwd: __dirname,
    stdio: 'pipe'
  });
  
  // ログ出力設定
  wsServer.stdout.on('data', data => 
    console.log('[WS Server]', data.toString().trim())
  );
  wsServer.stderr.on('data', data => 
    console.error('[WS Server Error]', data.toString().trim())
  );
  
  httpServer.stdout.on('data', data => 
    console.log('[HTTP Server]', data.toString().trim())
  );
  httpServer.stderr.on('data', data => 
    console.error('[HTTP Server Error]', data.toString().trim())
  );
  
  // ヘルスチェック実行
  console.log('🏥 Running health checks...');
  
  await waitForHealthy('ws://localhost:8080', {
    timeout: 30000,
    interval: 500,
    name: 'WebSocket Server',
    healthCheck: async (url) => {
      return new Promise((resolve) => {
        try {
          const ws = new WebSocket(url);
          ws.onopen = () => {
            ws.close();
            resolve(true);
          };
          ws.onerror = () => resolve(false);
          ws.onclose = () => resolve(false);
          
          // タイムアウト設定
          setTimeout(() => {
            ws.close();
            resolve(false);
          }, 1000);
        } catch {
          resolve(false);
        }
      });
    }
  });
  
  await waitForHealthy('http://localhost:3000/demo.html', {
    timeout: 30000,
    interval: 500,
    name: 'HTTP Server',
    healthCheck: async (url) => {
      try {
        const res = await fetch(url);
        return res.ok || res.status === 200;
      } catch {
        return false;
      }
    }
  });
  
  console.log('✅ All servers are healthy!');
  
  return {
    wsServer,
    httpServer,
    cleanup: () => {
      console.log('🧹 Cleaning up servers...');
      if (wsServer) wsServer.kill('SIGTERM');
      if (httpServer) httpServer.kill('SIGTERM');
    }
  };
}

// ========== ヘルスチェックヘルパー ==========

interface HealthCheckOptions {
  timeout: number;
  interval: number;
  name: string;
  healthCheck: (url: string) => Promise<boolean>;
}

async function waitForHealthy(url: string, options: HealthCheckOptions): Promise<void> {
  const { timeout, interval, name, healthCheck } = options;
  const start = Date.now();
  
  console.log(`⏳ Waiting for ${name} at ${url}...`);
  
  while (Date.now() - start < timeout) {
    try {
      const isHealthy = await healthCheck(url);
      if (isHealthy) {
        console.log(`✅ ${name} is ready!`);
        return;
      }
    } catch (error) {
      // エラーは無視して再試行
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error(`${name} failed to become healthy within ${timeout}ms`);
}

// ========== テストヘルパー ==========

export async function waitForKuzuDBInit(page: any) {
  await page.waitForFunction(
    () => document.getElementById('log')?.textContent?.includes('KuzuDB initialized'),
    { timeout: 10000 }
  );
}

export async function waitForWebSocketConnect(page: any) {
  await page.waitForFunction(
    () => document.getElementById('log')?.textContent?.includes('WebSocket connected'),
    { timeout: 10000 }
  );
}

export async function createUser(page: any, userName: string) {
  await page.fill('#userName', userName);
  await page.click('#createCustom');
}

export async function waitForUserInList(page: any, userName: string) {
  await page.waitForFunction(
    (name: string) => {
      const users = document.getElementById('users')?.textContent || '';
      return users.includes(name);
    },
    userName,
    { timeout: 5000 }
  );
}

export async function getUserList(page: any): Promise<string[]> {
  return await page.$$eval('#users .user', (users: Element[]) => 
    users.map(u => u.textContent?.trim() || '').filter(Boolean)
  );
}