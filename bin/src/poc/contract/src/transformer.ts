// Data Transformer - Handles schema transformations
import { log } from "../../../log/mod.ts";
import type { Result, TransformerError } from "./types.ts";

export class Transformer {
  private transforms = new Map<string, any>();
  
  async registerTransform(data: {
    from: string;
    to: string;
    script?: string;
    reverseScript?: string;
  }) {
    const key = `${data.from}->${data.to}`;
    this.transforms.set(key, {
      forward: data.script,
      reverse: data.reverseScript
    });
  }
  
  async transform(data: any, from: string, to: string, direction: "forward" | "reverse" = "forward"): Promise<Result<any, TransformerError>> {
    const key = `${from}->${to}`;
    const transform = this.transforms.get(key);
    
    if (!transform) {
      log("WARN", {
        uri: "contract.transformer.transform",
        message: "No custom transform found, transformation not supported",
        from,
        to
      });
      return {
        ok: false,
        error: {
          type: 'NO_TRANSFORM_AVAILABLE',
          message: `No transformation available from ${from} to ${to}`
        }
      };
    }
    
    const script = direction === "forward" ? transform.forward : transform.reverse;
    if (!script) {
      log("WARN", {
        uri: "contract.transformer.transform",
        message: "No script for direction, transformation not supported",
        direction,
        from,
        to
      });
      return {
        ok: false,
        error: {
          type: 'NO_TRANSFORM_AVAILABLE',
          message: `No ${direction} transformation script available from ${from} to ${to}`
        }
      };
    }
    
    // Execute in Worker for isolation
    try {
      const result = await this.executeInWorker(script, data);
      return { ok: true, data: result };
    } catch (error) {
      log("ERROR", {
        uri: "contract.transformer.transform",
        message: "Transform execution failed",
        error: error instanceof Error ? error.message : String(error),
        from,
        to,
        direction
      });
      return {
        ok: false,
        error: {
          type: 'TRANSFORM_EXECUTION_ERROR',
          message: `Transform execution failed: ${error instanceof Error ? error.message : String(error)}`
        }
      };
    }
  }
  
  private async executeInWorker(script: string, data: any): Promise<any> {
    // Simple eval-based execution for POC
    // In production, use proper sandboxing
    try {
      // Create a function that defines transform and then calls it
      const wrapper = new Function('data', script + '\nreturn transform(data);');
      return wrapper(data);
    } catch (error) {
      throw error;
    }
  }
  
  // Removed defaultTransform - no fallback behavior allowed
}