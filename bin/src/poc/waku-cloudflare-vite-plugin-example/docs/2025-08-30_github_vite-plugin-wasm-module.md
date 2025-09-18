---
url: https://github.com/hi-ogawa/vite-plugins/tree/main/packages/server-asset#vitepluginwasmmodule
saved_at: 2025-08-30T00:00:00Z
title: vitePluginWasmModule - WebAssembly Module Support for Vite
domain: github.com
---

# vitePluginWasmModule

## Purpose

This plugin enables `.wasm?module` import as a uniform syntax to initialize `WebAssembly.Module`.

## Key Features

- Supports WebAssembly module initialization
- Specifically designed for platforms like Cloudflare that require `.wasm` to be imported
- Provides uniform syntax across different build environments

## Usage Example

```typescript
import resvg_wasm from "./resvg.wasm?module";
```

### Build Mode Transformations

The plugin transforms the import differently based on the build mode:

#### Build Mode "fs" (File System)
```javascript
const resvg_wasm = new WebAssembly.Module(
  fs.readFileSync(
    fileURLToPath(new URL("resvg-Cjh1zH0p.wasm", import.meta.url).href)
  )
);
```

#### Build Mode "import"
```javascript
import __wasm_B7t_kJnM from "./resvg-Cjh1zH0p.wasm"
```

## Use Case

The plugin provides flexibility in how WebAssembly modules are imported and initialized across different build environments, making it particularly useful for:
- Cloudflare Workers deployments where `.wasm` files need special handling
- Cross-platform WebAssembly module initialization
- Consistent API for WebAssembly module imports regardless of the target environment