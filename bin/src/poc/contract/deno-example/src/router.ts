// Service Router - Routes calls through the contract service
import { Registry } from "./registry.ts";
import { Matcher } from "./matcher.ts";
import { Transformer } from "./transformer.ts";
import { log } from "../../../log/mod.ts";
import type { Result, RouterError } from "./types.ts";

export class Router {
  constructor(
    private registry: Registry,
    private matcher: Matcher,
    private transformer: Transformer
  ) {}
  
  async call(request: {
    from: string;
    data: any;
    preferences?: any;
  }): Promise<Result<any, RouterError>> {
    // Find best matching provider
    const provider = await this.matcher.findBestProvider(request.from, request.preferences);
    
    if (!provider || !provider.endpoint) {
      log("WARN", {
        uri: "contract.router.call",
        message: "No available providers found",
        consumer: request.from
      });
      return {
        ok: false,
        error: {
          type: 'NO_PROVIDER_FOUND',
          message: "No available providers"
        }
      };
    }
    
    // Transform request data
    const transformResult = await this.transformer.transform(
      request.data,
      request.from,
      provider.provider,
      "forward"
    );
    
    if (!transformResult.ok) {
      return {
        ok: false,
        error: {
          type: 'TRANSFORM_FAILED',
          message: `Failed to transform request: ${transformResult.error.message}`,
          details: transformResult.error
        }
      };
    }
    
    // Call actual provider
    let response;
    try {
      const result = await fetch(provider.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(transformResult.data)
      });
      
      if (!result.ok) {
        throw new Error(`Provider returned ${result.status}`);
      }
      
      response = await result.json();
    } catch (error) {
      log("ERROR", {
        uri: "contract.router.call",
        message: "Provider call failed",
        error: error instanceof Error ? error.message : String(error),
        providerUri: provider.provider,
        endpoint: provider.endpoint
      });
      return {
        ok: false,
        error: {
          type: 'PROVIDER_CALL_FAILED',
          message: `Provider call failed: ${error instanceof Error ? error.message : String(error)}`,
          details: error
        }
      };
    }
    
    // Transform response back
    const reverseTransformResult = await this.transformer.transform(
      response,
      provider.provider,
      request.from,
      "reverse"
    );
    
    if (!reverseTransformResult.ok) {
      return {
        ok: false,
        error: {
          type: 'TRANSFORM_FAILED',
          message: `Failed to transform response: ${reverseTransformResult.error.message}`,
          details: reverseTransformResult.error
        }
      };
    }
    
    return { ok: true, data: reverseTransformResult.data };
  }
}