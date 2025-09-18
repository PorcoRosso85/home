# RedwoodSDK DuckDB WASM Integration POC

This project is a proof-of-concept demonstrating the integration of **DuckDB WASM** with **RedwoodSDK** for client-side SQL analytics. Built upon the RedwoodSDK foundation, this POC showcases how to embed a full-featured analytical database directly in the browser using WebAssembly.

**Key highlights:**
- 🦆 **DuckDB WASM**: Full SQL analytics engine running client-side
- 🚀 **Zero Server Overhead**: All queries execute locally in the browser
- ⚡ **High Performance**: WASM-powered analytical processing
- 🔧 **Nix-Managed Assets**: DuckDB WASM files delivered via Nix flake
- 🌐 **RedwoodSDK Integration**: Full-stack web framework with SSR and RSC

This starter includes:
- **Vite** development server with HMR
- **DuckDB WASM** for client-side analytics (MVP version)
- **Database** (Prisma via D1) for persistent storage
- **Session Management** (via DurableObjects)
- **Passkey Authentication** (WebAuthn)
- **Object Storage** (via R2)

## Quick Start

### Prerequisites
- Nix package manager with flakes enabled
- Git

### Development Setup

**Option 1: Using Nix (Recommended)**
```shell
# Clone and enter the project
git clone <your-repo-url>
cd redwoodsdk-duckdb

# Enter Nix development shell (automatically links DuckDB WASM assets)
nix develop

# Install dependencies and start development server
pnpm install
pnpm run dev
```

**Option 2: Manual Setup**
```shell
# If you prefer npm/yarn without Nix
npm install  # or yarn install
npm run dev  # Note: DuckDB assets won't be available without Nix
```

### How DuckDB Assets Are Managed

This project uses a **Nix flake** to automatically manage DuckDB WASM assets:

- **Source**: DuckDB WASM assets are fetched from the official npm package `@duckdb/duckdb-wasm`
- **Version**: Currently using `1.28.1-dev106.0` (MVP build)
- **Location**: Assets are symlinked to `public/duckdb/` during `nix develop`
- **Files Included** (4 files total):
  - `duckdb-mvp.wasm` (~36MB) - Main WebAssembly module
  - `duckdb-browser-mvp.worker.js` (~820KB) - Web Worker for browser execution
  - `duckdb-browser.mjs` (~30KB) - ES module interface
  - `duckdb-mvp.wasm.map` (optional) - Source map for debugging

The Nix flake ensures reproducible builds and eliminates the need to commit large binary files to your repository.

### Verification Steps

After setup, verify that DuckDB WASM is properly configured:

1. **Check Asset Availability**:
```shell
# Verify symlink is created
ls -la public/duckdb/
# Should show 4 main files (*.wasm, *.worker.js, *.mjs, *.map)
```

2. **Browser Verification**:
   - Start dev server: `pnpm dev`
   - Open http://localhost:5173
   - Click "🔍 Self-Diagnosis" button
   - Verify all 4 assets load successfully
   - Open DevTools Network tab and confirm:
     - All assets load from `/duckdb/` (not CDN)
     - Status 200 for all files
     - No external CDN requests

3. **Query Test**:
   - Execute default query: `SELECT 1 + 1 as result`
   - Should return `[{"result": 2}]`

### Important: Symlink vs Copy for Deployment

**Development** (using symlink):
- `nix develop` creates a symlink: `public/duckdb -> /nix/store/...`
- Benefits: No file duplication, automatic updates
- Drawback: Only works in Nix environment

**Production Deployment** (requires copy):
```shell
# For deployment, copy assets instead of symlink
rm -rf public/duckdb
cp -r $(readlink -f public/duckdb) public/duckdb

# Or build with Nix and copy
nix build .#duckdb-wasm
cp -r result/wasm/duckdb public/duckdb
```

**Why copy for deployment?**
- Symlinks to `/nix/store` won't work outside Nix environment
- Cloud platforms need actual files in the deployment bundle
- Ensures assets are included in build artifacts

### Access Your Application

Point your browser to `http://localhost:5173/` to see the DuckDB integration in action. You'll find:
- A SQL query interface powered by DuckDB WASM
- Sample queries to test analytical capabilities
- Real-time query execution without server round-trips

## Features

### Client-Side SQL Analytics
This POC demonstrates **DuckDB WASM** running entirely in the browser:

- **No Server Required**: All SQL queries execute locally using WebAssembly
- **Full SQL Support**: Window functions, joins, aggregations, JSON operations, and more
- **High Performance**: Columnar processing optimized for analytical workloads
- **Memory Efficient**: Data processed in-browser without network overhead

### Interactive Query Interface
The included `DuckDBCell` component provides:

- **SQL Editor**: Multi-line SQL input with syntax highlighting awareness
- **Keyboard Shortcuts**: Ctrl/Cmd + Enter for quick execution
- **Real-time Results**: JSON-formatted query results display
- **Error Handling**: Clear error messages for debugging queries
- **Status Indicators**: Visual feedback for loading, ready, and error states

### Sample Analytical Queries
Try these queries to explore DuckDB's capabilities:

```sql
-- Generate sample data
SELECT * FROM range(1000) AS t(id);

-- Create and query tables
CREATE TABLE sales AS 
SELECT 
  id,
  'Product_' || (id % 10) AS product_name,
  (random() * 1000)::INTEGER AS revenue,
  ('2024-01-01'::DATE + INTERVAL (id % 365) DAY) AS sale_date
FROM range(10000) AS t(id);

-- Analytical queries
SELECT 
  product_name,
  COUNT(*) AS sales_count,
  SUM(revenue) AS total_revenue,
  AVG(revenue) AS avg_revenue
FROM sales 
GROUP BY product_name 
ORDER BY total_revenue DESC;

-- Window functions
SELECT 
  sale_date,
  revenue,
  AVG(revenue) OVER (
    ORDER BY sale_date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS moving_avg_7day
FROM sales 
ORDER BY sale_date 
LIMIT 100;
```

### Local WASM Execution
Key benefits of the WASM approach:

- **Privacy**: Data never leaves the client browser
- **Latency**: Sub-millisecond query execution for small-medium datasets
- **Scalability**: No server-side query processing overhead
- **Offline Capable**: Works without internet connection once assets are loaded

## Technical Details

### Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vite + React  │    │  DuckDB WASM    │    │  Nix Flake      │
│                 │    │                 │    │                 │
│ • UI Components │◄──►│ • SQL Engine    │◄───│ • Asset Mgmt    │
│ • State Mgmt    │    │ • WASM Runtime  │    │ • Reproducible  │
│ • RedwoodSDK    │    │ • Web Workers   │    │ • Version Lock  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### DuckDB WASM Configuration
This project uses the **MVP (Minimum Viable Product)** build of DuckDB WASM:

- **Target**: `duckdb-mvp.wasm` - Optimized for broad browser compatibility
- **Worker**: `duckdb-browser-mvp.worker.js` - Web Worker for non-blocking execution
- **Interface**: `duckdb-browser.mjs` - ES module API for modern JavaScript

### Alternative Builds (Future Consideration)
DuckDB WASM provides other optimized builds:

- **EH (Exception Handling)**: `duckdb-eh.wasm` - Better error handling, requires newer browsers
- **COI (Cross-Origin Isolated)**: `duckdb-coi.wasm` - Highest performance with SharedArrayBuffer

**Note**: EH and COI versions require **COOP/COEP headers** (Cross-Origin-Opener-Policy/Cross-Origin-Embedder-Policy) to enable SharedArrayBuffer and advanced browser features. These headers are not currently configured in this POC but can be added for production deployments requiring maximum performance.

### Integration with RedwoodSDK
- **Vite Plugin**: Seamless asset serving and HMR support
- **SSR Compatible**: DuckDB components use client-side rendering
- **Cloudflare Workers**: Compatible with Cloudflare's worker runtime
- **Progressive Enhancement**: Graceful fallback when WASM isn't supported

## Deploying your app

### Wrangler Setup

Within your project's `wrangler.jsonc`:

- Replace the `__change_me__` placeholders with a name for your application

- Create a new D1 database:

```shell
npx wrangler d1 create my-project-db
```

Copy the database ID provided and paste it into your project's `wrangler.jsonc` file:

```jsonc
{
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "my-project-db",
      "database_id": "your-database-id",
    },
  ],
}
```

### Authentication Setup

For authentication setup and configuration, including optional bot protection, see the [Authentication Documentation](https://docs.rwsdk.com/core/authentication).

## License & Attribution

### DuckDB License
This project integrates [DuckDB WASM](https://github.com/duckdb/duckdb-wasm), which is licensed under the MIT License.

**DuckDB Copyright Notice:**
```
Copyright 2018-2024 DuckDB Labs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

**Acknowledgments:**
- DuckDB Team for creating an exceptional analytical database and WASM implementation
- [DuckDB WASM Documentation](https://duckdb.org/docs/api/wasm/overview)
- [DuckDB GitHub Repository](https://github.com/duckdb/duckdb)

### Project License
This POC project is licensed under the MIT License, same as the underlying RedwoodSDK framework.

## Further Reading

### RedwoodSDK Resources
- [RedwoodSDK Documentation](https://docs.rwsdk.com/) - Complete framework documentation
- [RedwoodSDK GitHub](https://github.com/redwoodjs/redwoodsdk) - Source code and examples
- [Cloudflare Workers Secrets](https://developers.cloudflare.com/workers/runtime-apis/secrets/) - Production security

### DuckDB & WASM Resources
- [DuckDB WASM Overview](https://duckdb.org/docs/api/wasm/overview) - Official WASM documentation
- [DuckDB SQL Reference](https://duckdb.org/docs/sql/introduction) - Complete SQL syntax guide
- [DuckDB Performance Guide](https://duckdb.org/docs/guides/performance/overview) - Optimization techniques
- [WebAssembly Performance](https://web.dev/webassembly/) - Understanding WASM in browsers

### Development & Deployment
- [Nix Flakes Tutorial](https://nixos.wiki/wiki/Flakes) - Managing reproducible development environments
- [Vite Guide](https://vitejs.dev/guide/) - Modern frontend tooling
- [SharedArrayBuffer and COOP/COEP](https://web.dev/coop-coep/) - Advanced browser security features
