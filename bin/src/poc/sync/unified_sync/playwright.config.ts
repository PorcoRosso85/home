import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  
  // タイムアウト設定
  timeout: 60000,
  
  // リトライ設定（確実性向上）
  retries: process.env.CI ? 2 : 0,
  
  // ワーカー数
  workers: process.env.CI ? 1 : undefined,
  
  use: {
    // 実際のブラウザ環境
    browserName: 'chromium',
    
    // KuzuDB WASMに必要な設定
    launchOptions: {
      args: [
        '--enable-features=SharedArrayBuffer',
        '--enable-features=WebAssemblyThreads'
      ]
    },
    
    // Cross-Origin Isolation設定
    contextOptions: {
      ignoreHTTPSErrors: true,
    },
    
    // トレース記録（デバッグ用）
    trace: 'on-first-retry',
    
    // スクリーンショット（失敗時）
    screenshot: 'only-on-failure',
    
    // ビデオ録画（失敗時）
    video: 'retain-on-failure',
  },
  
  // レポーター設定
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/html' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  
  // テスト結果の出力先
  outputDir: 'test-results/artifacts',
  
  // グローバルセットアップ/ティアダウンは使用しない
  // （test-fixtures.tsで管理）
});