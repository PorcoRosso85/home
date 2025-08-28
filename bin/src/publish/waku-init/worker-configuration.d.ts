declare namespace Cloudflare {
  interface Env {
    // R2 bucket binding
    DATA_BUCKET: R2Bucket;
    
    // D1 Database binding
    DB: D1Database;
    
    // Environment variables
    ENABLE_WASM_FROM_R2: string;
    R2_PUBLIC_URL: string;
    R2_WASM_URL: string;
  }
}

interface Env extends Cloudflare.Env {}