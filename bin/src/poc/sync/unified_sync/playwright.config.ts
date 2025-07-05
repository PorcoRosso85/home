import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
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
    }
  },
  
  webServer: {
    command: 'npm run serve',
    port: 3000,
    reuseExistingServer: true,
  }
});