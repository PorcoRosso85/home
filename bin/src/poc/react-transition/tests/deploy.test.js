// デプロイプロセスのテスト【RED】
import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { readFileSync } from 'fs';

describe('Deploy Configuration', () => {
  it('should have package.json with build script', () => {
    expect(existsSync('./package.json')).toBe(true);
    
    const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));
    expect(packageJson.scripts).toBeDefined();
    expect(packageJson.scripts.build).toBeDefined();
  });

  it('should have vite configuration', () => {
    expect(existsSync('./vite.config.mts')).toBe(true);
  });

  it('should have React app entry point', () => {
    // Reactアプリケーションの基本ファイルが存在する
    expect(existsSync('./index.html')).toBe(true);
    expect(existsSync('./src')).toBe(true);
    expect(existsSync('./src/main.tsx')).toBe(true);
    expect(existsSync('./src/App.tsx')).toBe(true);
  });

  it('should have flake configuration for deployment', () => {
    expect(existsSync('./flake.nix')).toBe(true);
    
    const flakeContent = readFileSync('./flake.nix', 'utf-8');
    expect(flakeContent).toContain('apps');
  });

  it('should have successful build output', async () => {
    // ビルド成功でdistディレクトリが生成されている
    expect(existsSync('./dist')).toBe(true);
    expect(existsSync('./dist/index.html')).toBe(true);
    expect(existsSync('./dist/assets')).toBe(true);
    // ソースファイルも存在している
    expect(existsSync('./index.html')).toBe(true);
    expect(existsSync('./src/main.tsx')).toBe(true);
  });
});