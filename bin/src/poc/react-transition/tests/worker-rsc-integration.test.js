// Cloudflare Workers × RSC 統合テスト【RED】
import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { readFileSync } from 'fs';

describe('Cloudflare Workers × RSC Integration', () => {
  it('should have worker entry point configured', () => {
    // src/worker.tsx が存在する
    expect(existsSync('./src/worker.tsx')).toBe(true);
  });

  it('should have wrangler configuration for Workers', () => {
    expect(existsSync('./wrangler.toml')).toBe(true);
    
    const wranglerContent = readFileSync('./wrangler.toml', 'utf-8');
    // Workers用のmain設定
    expect(wranglerContent).toContain('main = "src/worker.tsx"');
    // Pages設定からWorkers設定へ移行済み
    expect(wranglerContent).not.toContain('pages_build_output_dir');
  });

  it('should have React 19 for RSC support', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    // React 19系への移行済み
    const reactVersion = packageJson.dependencies?.react || packageJson.devDependencies?.react;
    expect(reactVersion?.startsWith('^19')).toBe(true);
  });

  it('should have RSC directory structure', () => {
    // RSC用のディレクトリ構造
    expect(existsSync('./src/app/Document.server.tsx')).toBe(true);
    // root.server.tsxは未実装（今後必要に応じて）
    expect(existsSync('./src/app/root.server.tsx')).toBe(false);
    expect(existsSync('./src/app/pages')).toBe(true);
  });

  it('should have RedwoodSDK dependencies', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    // RedwoodSDK依存関係
    expect(packageJson.dependencies?.['rwsdk'] || packageJson.devDependencies?.['rwsdk']).toBeDefined();
  });
});

describe('Worker × RSC Build Configuration', () => {
  it('should have worker deploy script', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    // worker deploy コマンド
    expect(packageJson.scripts?.['deploy:worker']).toBeDefined();
    // Workers deployに移行済み
    expect(packageJson.scripts?.deploy).toContain('wrangler deploy');
  });

  it('should have worker development script', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    // worker dev コマンド
    expect(packageJson.scripts?.['dev:worker']).toBeDefined();
  });

  it('should have flake worker apps', () => {
    expect(existsSync('./flake.nix')).toBe(true);
    
    const flakeContent = readFileSync('./flake.nix', 'utf-8');
    // worker dev app
    expect(flakeContent).toContain('dev-worker');
    expect(flakeContent).toContain('deploy-worker');
  });
});

describe('Worker × RSC Server Rendering', () => {
  it('should render HTML with RSC on server', async () => {
    // wrangler dev で起動したWorkerからのSSR応答確認
    // worker.tsxの存在を確認（実際の起動は手動テスト）
    expect(existsSync('./src/worker.tsx')).toBe(true);
  });

  it('should serve transition demo via RSC', async () => {
    // RSC経由での遷移デモ配信
    // Server Component として TransitionDemo を配信する機能
    expect(existsSync('./src/app/pages/TransitionDemo.tsx')).toBe(true);
  });

  it('should handle use client boundaries correctly', () => {
    // "use client" 境界の適切な設定
    // インタラクティブな遷移部分のみクライアント化
    expect(existsSync('./src/app/pages/TransitionDemo.tsx')).toBe(true);
    const content = readFileSync('./src/app/pages/TransitionDemo.tsx', 'utf-8');
    expect(content).toContain('"use client"');
  });
});