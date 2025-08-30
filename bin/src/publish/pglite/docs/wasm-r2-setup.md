# DuckDB WASM + R2 Setup Guide

## Overview
This boilerplate includes a DuckDB WASM demo that can query data files (parquet, CSV) either from local URLs or from Cloudflare R2 storage.

## Features
- **DuckDB WASM from CDN**: Loads DuckDB WASM directly from jsDelivr CDN
- **Query any data source**: Works with local files, R2, or any CORS-enabled URL
- **Environment-based toggle**: Enable/disable R2 features via environment variables
- **No server-side processing**: All queries run in the browser

## Setup Instructions

### 1. Local Development
```bash
# Start dev server
npm run dev
```

DuckDB WASM loads automatically from CDN.
You can query any publicly accessible parquet/CSV files.

### 2. R2 Setup (Optional)

#### Create R2 Bucket
```bash
# Create bucket
npm run r2:create

# Upload your data files (parquet, CSV)
wrangler r2 object put waku-data/mydata.parquet --file=./data/mydata.parquet

# Verify upload  
npm run r2:list
```

#### Configure Environment Variables
```bash
# In wrangler.toml or .env
ENABLE_WASM_FROM_R2=true
R2_PUBLIC_URL=https://your-r2-domain.example.com
```

#### Set up Custom Domain (Required for CORS)
1. Go to Cloudflare Dashboard > R2
2. Select your bucket
3. Settings > Custom Domains
4. Add your domain

#### Configure CORS Policy
```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }
]
```

## Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_WASM_FROM_R2` | boolean | `false` | Enable R2 loading option |
| `R2_PUBLIC_URL` | string | `""` | R2 custom domain URL |

## Component Usage

The `<DuckDBR2Demo>` component provides:
- SQL query interface
- DuckDB WASM loaded from CDN
- Support for querying R2-hosted data
- Error handling and status display

```tsx
<DuckDBR2Demo 
  enableR2={enableWasmFromR2} 
  r2Url={r2PublicUrl} 
/>
```

## Example Queries

```sql
-- Query local parquet file
SELECT * FROM '/data/sample.parquet' LIMIT 10;

-- Query R2-hosted parquet  
SELECT * FROM 'https://your-r2-domain.com/data.parquet' LIMIT 10;

-- Aggregate query
SELECT COUNT(*) as total, AVG(price) as avg_price 
FROM read_parquet('https://your-r2-domain.com/sales.parquet');
```

## Notes
- DuckDB WASM is ~45MB and loads from CDN on first visit
- R2 data access requires proper CORS configuration
- All processing happens in the browser (no server costs)
- Supports parquet, CSV, and JSON formats