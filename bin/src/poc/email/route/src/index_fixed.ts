/**
 * Email Archive Worker
 * Archives incoming emails to in-memory storage for testing
 * No external dependencies - pure Cloudflare Worker
 */

// In-memory storage for testing
const storage = new Map<string, Uint8Array>();

export type Env = {
  STORAGE_TYPE?: string;
  BUCKET_NAME?: string;
}

export type EmailMessage = {
  from: string;
  to: string;
  headers: Headers;
  raw: () => Promise<ArrayBuffer>;
  setReject?: (reason: string) => void;
  forward?: (to: string) => Promise<void>;
}

// Result types for error handling
export type ProcessResult = 
  | { ok: true; data: { status: string; message: string; key: string } }
  | { ok: false; error: { status: string; message: string } };

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Test endpoint for email submission
    if (url.pathname === "/__email") {
      const data = await request.json() as {
        from: string;
        to: string;
        headers?: Record<string, string>;
        body?: string;
      };
      
      const message: EmailMessage = {
        from: data.from,
        to: data.to,
        headers: new Headers(data.headers || {}),
        async raw() {
          return new TextEncoder().encode(data.body || "").buffer;
        }
      };
      
      // Process email
      const response = await this.email(message, env, ctx);
      return response;
    }
    
    // Storage inspection endpoint
    if (url.pathname === "/__storage") {
      const contents = Array.from(storage.entries()).map(([k, v]) => ({
        key: k,
        size: v.length
      }));
      return new Response(JSON.stringify(contents, null, 2), {
        headers: { "Content-Type": "application/json" }
      });
    }
    
    // Health check endpoint
    if (url.pathname === "/__health") {
      return new Response(JSON.stringify({
        status: 'ok',
        timestamp: new Date().toISOString(),
        mode: 'in-memory-storage',
        storageSize: storage.size
      }, null, 2), {
        headers: { "Content-Type": "application/json" }
      });
    }
    
    return new Response("Email Archive Worker", {
      headers: { "Content-Type": "text/plain" }
    });
  },
  
  async email(message: EmailMessage, env: Env, ctx: ExecutionContext): Promise<Response> {
    // NOTE: Structured logging would require telemetry module integration
    // For POC, returning structured response instead of console.log
    
    const result = await processEmail(message);
    
    if (result.ok) {
      return new Response(JSON.stringify(result.data), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    } else {
      return new Response(JSON.stringify(result.error), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};

async function processEmail(message: EmailMessage): Promise<ProcessResult> {
  try {
    // Get raw email content
    const rawEmail = await message.raw();
    
    // Extract metadata
    const metadata = {
      messageId: message.headers.get("message-id") || `test-${Date.now()}`,
      from: message.from,
      to: message.to,
      subject: message.headers.get("subject") || "No subject",
      receivedAt: new Date().toISOString(),
      size: rawEmail.byteLength
    };
    
    // Generate storage keys with date-based path
    const date = new Date();
    const datePrefix = `emails/${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
    const baseKey = `${datePrefix}/${metadata.messageId}`;
    
    // Store in memory
    storage.set(`${baseKey}.eml`, new Uint8Array(rawEmail));
    storage.set(`${baseKey}.json`, new TextEncoder().encode(JSON.stringify(metadata, null, 2)));
    
    return {
      ok: true,
      data: {
        status: "success",
        message: "Email archived successfully",
        key: baseKey
      }
    };
    
  } catch (error) {
    return {
      ok: false,
      error: {
        status: "error",
        message: error instanceof Error ? error.message : "Unknown error"
      }
    };
  }
}