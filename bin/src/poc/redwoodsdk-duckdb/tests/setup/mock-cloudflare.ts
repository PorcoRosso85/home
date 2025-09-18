// Mock for cloudflare:workers module
export const env = {
  WEBAUTHN_RP_ID: 'localhost',
  WEBAUTHN_APP_NAME: 'Test App',
  DB: {} as any,
  SESSION_DURABLE_OBJECT: {} as any,
  ASSETS: {} as any,
  KV: {} as any,
  BUCKET: {} as any
};

export const ExecutionContext = class {
  waitUntil(promise: Promise<any>) {
    // Mock implementation
  }
  
  passThroughOnException() {
    // Mock implementation
  }
};

export const Response = globalThis.Response;
export const Request = globalThis.Request;
export const Headers = globalThis.Headers;