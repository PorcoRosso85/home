# Vite RSC Examples Comparison

## starter vs starter-cf-single

### Architecture Differences

#### `starter` (Standard Node.js)
- **3 separate environments**: rsc, ssr, client
- **Deployment**: Traditional Node.js server
- **Entry points**:
  - `entry.rsc.tsx` - RSC handler
  - `entry.ssr.tsx` - SSR handler  
  - `entry.browser.tsx` - Client hydration
- **Uses**: `bootstrapScriptContent` directly

#### `starter-cf-single` (Cloudflare Workers)
- **Single worker deployment**: RSC and SSR in same worker
- **Deployment**: Cloudflare Workers with `nodejs_als` flag
- **Build**: SSR builds into `dist/rsc/ssr` directory
- **Key config**: `loadModuleDevProxy: true`
- **Special handling**: SSR environment marked as `keepProcessEnv: false`

### Key Takeaways

1. **For Cloudflare Workers**: Use `starter-cf-single` pattern
2. **Bootstrap handling**: Workers need special handling for `bootstrapScriptContent`
3. **Build structure**: SSR must be inside RSC directory for Workers
4. **Compatibility**: Requires `nodejs_als` flag for AsyncLocalStorage

### Our Implementation Issue

We mixed patterns from both examples:
- Used `starter-cf-single` config (good ✓)
- But used `starter` bootstrap pattern (caused issues ✗)

### Solution Applied

Convert `bootstrapScriptContent` (JS code string) to `bootstrapModules` (URL array):
```typescript
// Extract module path from 'import("/assets/xxx.js")'
const match = bootstrapScriptContent.match(/import\("([^"]+)"\)/);
if (match) {
  bootstrapModules = [match[1]];
}
```

This bridges the gap between Vite's output format and React's SSR API expectations.