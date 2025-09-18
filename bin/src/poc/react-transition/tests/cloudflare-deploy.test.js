// Cloudflare Pagesデプロイ設定のテスト【RED】
import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { readFileSync } from 'fs';

describe('Cloudflare Pages Deploy Configuration', () => {
  it('should have wrangler configuration for Pages', () => {
    // wrangler.toml設定ファイルが存在する
    expect(existsSync('./wrangler.toml')).toBe(true);
  });

  it('should have deployment-ready build output', () => {
    // デプロイ用のdistディレクトリが存在する
    expect(existsSync('./dist')).toBe(true);
    expect(existsSync('./dist/index.html')).toBe(true);
    
    // SPAルーティング用の_redirects設定
    expect(existsSync('./dist/_redirects')).toBe(true);
  });

  it('should have package.json with deploy command', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    // デプロイコマンドが定義されている
    expect(packageJson.scripts.deploy).toBeDefined();
  });

  it('should have flake configuration for Pages deploy', () => {
    expect(existsSync('./flake.nix')).toBe(true);
    
    const flakeContent = readFileSync('./flake.nix', 'utf-8');
    expect(flakeContent).toContain('apps');
    // デプロイアプリが含まれている
    expect(flakeContent).toContain('deploy');
  });

  it('should have compatible build for static hosting', () => {
    // ビルド出力が静的ホスティング用になっている
    expect(existsSync('./dist')).toBe(true);
    
    // index.htmlが存在し、Reactアプリが組み込まれている
    if (existsSync('./dist/index.html')) {
      const indexContent = readFileSync('./dist/index.html', 'utf-8');
      expect(indexContent).toContain('id="root"');
    }
  });
});