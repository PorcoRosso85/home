/**
 * Email Worker
 * Pure Cloudflare Email Worker implementation
 * Handles email routing logic without storage
 */

export type Env = {
  // Environment bindings can be added here
}

export type ForwardableEmailMessage = {
  from: string;
  to: string;
  headers: Headers;
  raw: () => Promise<ArrayBuffer>;
  setReject: (reason: string) => void;
  forward: (to: string, headers?: Headers) => Promise<void>;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("Email Worker", {
      headers: { "Content-Type": "text/plain" }
    });
  },
  
  async email(message: ForwardableEmailMessage, env: Env, ctx: ExecutionContext): Promise<void> {
    // Basic email processing logic
    // This is where you would implement your email routing rules
    
    // Example: Simple allowlist
    const allowlist = ["trusted@example.com", "friend@example.com"];
    
    if (!allowlist.includes(message.from)) {
      message.setReject("Address not allowed");
      return;
    }
    
    // Forward to default inbox if allowed
    await message.forward("inbox@example.com");
  }
};