import { describe, it, expect } from 'vitest';

describe('Deployment Configuration', () => {
  it('should have valid wrangler configuration', async () => {
    // Read and verify wrangler.toml exists and has required fields
    const fs = await import('fs/promises');
    const wranglerConfig = await fs.readFile('./wrangler.toml', 'utf-8');
    
    expect(wranglerConfig).toContain('name = "react-ssr-worker-reference"');
    expect(wranglerConfig).toContain('main = "src/worker.tsx"');
    expect(wranglerConfig).toContain('compatibility_date = "2024-09-23"');
    expect(wranglerConfig).toContain('nodejs_compat');
  });

  it('should have React 19 dependencies', async () => {
    const fs = await import('fs/promises');
    const packageJson = JSON.parse(await fs.readFile('./package.json', 'utf-8'));
    
    expect(packageJson.dependencies.react).toBe('^19.0.0');
    expect(packageJson.dependencies['react-dom']).toBe('^19.0.0');
    expect(packageJson.name).toBe('react-ssr-worker-reference');
  });

  it('should have working src/worker.tsx entry point', async () => {
    const fs = await import('fs/promises');
    const workerCode = await fs.readFile('./src/worker.tsx', 'utf-8');
    
    // Verify the successful SSR approach is in place
    expect(workerCode).toContain('export default {');
    expect(workerCode).toContain('async fetch(request: Request, env: any)');
    expect(workerCode).toContain('env.ASSETS');
    expect(workerCode).not.toContain('renderToString'); // Should use direct HTML strings
  });

  it('should have pre-built assets directory', async () => {
    const fs = await import('fs/promises');
    
    // Verify dist directory exists with assets
    const distExists = await fs.access('./dist').then(() => true).catch(() => false);
    expect(distExists).toBe(true);
    
    const assetsExists = await fs.access('./dist/assets').then(() => true).catch(() => false);
    expect(assetsExists).toBe(true);
  });

  it('should have proper flake configuration', async () => {
    const fs = await import('fs/promises');
    const flakeNix = await fs.readFile('./flake.nix', 'utf-8');
    
    expect(flakeNix).toContain('nodejs_22');
    expect(flakeNix).toContain('flake-parts');
    expect(flakeNix).toContain('readme.enable = true');
    expect(flakeNix).toContain('deploy');
  });
});

describe('Success Factors Verification', () => {
  it('should implement all identified success factors', async () => {
    const fs = await import('fs/promises');
    
    // Success Factor 1: React 19.0.0
    const packageJson = JSON.parse(await fs.readFile('./package.json', 'utf-8'));
    expect(packageJson.dependencies.react).toBe('^19.0.0');
    
    // Success Factor 2: Direct HTML string rendering approach
    const workerCode = await fs.readFile('./src/worker.tsx', 'utf-8');
    expect(workerCode).toContain('function App()');
    expect(workerCode).toContain('return `'); // Template literal for HTML
    
    // Success Factor 3: Cloudflare Workers compatibility
    const wranglerConfig = await fs.readFile('./wrangler.toml', 'utf-8');
    expect(wranglerConfig).toContain('compatibility_date = "2024-09-23"');
    expect(wranglerConfig).toContain('nodejs_compat');
    
    // Success Factor 4: Node.js 22
    const flakeNix = await fs.readFile('./flake.nix', 'utf-8');
    expect(flakeNix).toContain('nodejs_22');
    
    // Success Factor 5: Asset management
    expect(wranglerConfig).toContain('[assets]');
    expect(wranglerConfig).toContain('directory = "dist/assets"');
  });
});