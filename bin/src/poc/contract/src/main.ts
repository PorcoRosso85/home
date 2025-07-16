// Contract Service - Main Entry Point
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { Router } from "./router.ts";
import { Registry } from "./registry.ts";
import { Matcher } from "./matcher.ts";
import { Transformer } from "./transformer.ts";
import { initDatabase } from "./kuzu_wrapper.ts";
import { log } from "../../../log/mod.ts";

// Initialize components
const db = await initDatabase();
const registry = new Registry(db);
const matcher = new Matcher(db);
const transformer = new Transformer();
const router = new Router(registry, matcher, transformer);

// Register default transforms for testing
await transformer.registerTransform({
  from: "ui/dashboard/v2",
  to: "services/weather/v1",
  script: `
    function transform(data) {
      const result = {};
      if (data.city !== undefined) result.location = data.city;
      return result;
    }
  `,
  reverseScript: `
    function transform(data) {
      const result = {};
      if (data.temperature !== undefined) result.temp = data.temperature;
      if (data.humidity !== undefined) result.humid = data.humidity;
      if (data.location !== undefined) result.city = data.location;
      return result;
    }
  `
});

// Register additional transforms for other services
await transformer.registerTransform({
  from: "services/search/v1",
  to: "services/weather/v1",
  script: `
    function transform(data) {
      const result = {};
      if (data.search_text !== undefined) result.query = data.search_text;
      if (data.max_results !== undefined) result.limit = data.max_results;
      return result;
    }
  `,
  reverseScript: `
    function transform(data) {
      const result = {};
      // Simple passthrough for now
      return data;
    }
  `
});

// JSON-RPC2 error codes
const RPC_ERRORS = {
  PARSE_ERROR: { code: -32700, message: "Parse error" },
  INVALID_REQUEST: { code: -32600, message: "Invalid Request" },
  METHOD_NOT_FOUND: { code: -32601, message: "Method not found" },
  INVALID_PARAMS: { code: -32602, message: "Invalid params" },
  INTERNAL_ERROR: { code: -32603, message: "Internal error" },
  // Custom errors
  NO_PROVIDER: { code: -32001, message: "No compatible provider found" },
  SCHEMA_MISMATCH: { code: -32002, message: "Schema transformation failed" },
  INVALID_SCHEMA: { code: -32003, message: "Invalid schema format" }
};

// JSON-RPC2 methods
const methods: Record<string, (params: any) => Promise<any>> = {
  // Register provider or consumer
  "contract.register": async (params) => {
    // Validate type parameter
    if (!params.type) {
      throw new Error("Missing required parameter: type");
    }
    
    if (params.type === "provider") {
      // Validate required schema paths
      if (!params.inputSchemaPath) {
        throw new Error("Missing required parameter: inputSchemaPath");
      }
      if (!params.outputSchemaPath) {
        throw new Error("Missing required parameter: outputSchemaPath");
      }
      if (typeof params.inputSchemaPath !== "string") {
        throw new Error("Invalid parameter type: inputSchemaPath must be a string");
      }
      if (typeof params.outputSchemaPath !== "string") {
        throw new Error("Invalid parameter type: outputSchemaPath must be a string");
      }
      
      const result = await registry.registerProvider({
        uri: params.uri,
        inputSchemaPath: params.inputSchemaPath,
        outputSchemaPath: params.outputSchemaPath,
        endpoint: params.endpoint,
        metadata: params.metadata
      });
      
      if (!result.ok) {
        // Convert RegistryError to appropriate RPC error
        if (result.error.type === 'SCHEMA_FILE_NOT_FOUND') {
          throw new Error(result.error.message);
        } else if (result.error.type === 'INVALID_JSON') {
          throw new Error(result.error.message);
        } else if (result.error.type === 'INVALID_SCHEMA') {
          throw new Error(`Invalid schema format: ${result.error.message}`);
        }
        throw new Error(result.error.message);
      }
      
      // Find matching consumers
      const matches = await matcher.findConsumersFor(params.uri);
      return {
        ...result.data,
        matches: matches.map(m => ({
          consumer: m.consumer,
          compatibility: 0.9, // TODO: Calculate real compatibility
          autoTransform: true
        }))
      };
    } else if (params.type === "consumer") {
      // Validate required expects schema paths
      if (!params.expectsInputSchemaPath) {
        throw new Error("Missing required parameter: expectsInputSchemaPath");
      }
      if (!params.expectsOutputSchemaPath) {
        throw new Error("Missing required parameter: expectsOutputSchemaPath");
      }
      if (typeof params.expectsInputSchemaPath !== "string") {
        throw new Error("Invalid parameter type: expectsInputSchemaPath must be a string");
      }
      if (typeof params.expectsOutputSchemaPath !== "string") {
        throw new Error("Invalid parameter type: expectsOutputSchemaPath must be a string");
      }
      
      const result = await registry.registerConsumer({
        uri: params.uri,
        expectsInputSchemaPath: params.expectsInputSchemaPath,
        expectsOutputSchemaPath: params.expectsOutputSchemaPath
      });
      
      if (!result.ok) {
        // Convert RegistryError to appropriate RPC error
        if (result.error.type === 'SCHEMA_FILE_NOT_FOUND') {
          throw new Error(result.error.message);
        } else if (result.error.type === 'INVALID_JSON') {
          throw new Error(result.error.message);
        } else if (result.error.type === 'INVALID_SCHEMA') {
          throw new Error(`Invalid schema format: ${result.error.message}`);
        }
        throw new Error(result.error.message);
      }
      
      // Find available providers
      const providers = await matcher.findProvidersFor(params.uri);
      return {
        ...result.data,
        providers: providers.map(p => ({
          uri: p.provider,
          endpoint: p.endpoint,
          transformPreview: {
            forward: { city: "location" }, // TODO: Get actual transform
            reverse: { temp: "temperature", humidity: "humid", location: "city" }
          }
        }))
      };
    }
    throw new Error("Invalid registration type: must be 'provider' or 'consumer'");
  },
  
  // Call a service with automatic transformation
  "contract.call": async (params) => {
    // Validate required parameters
    if (!params.from) {
      throw new Error("Missing required parameter: from");
    }
    
    const startTime = Date.now();
    const result = await router.call({
      from: params.from,
      data: params.data,
      preferences: params.preferences
    });
    
    if (!result.ok) {
      if (result.error.type === 'NO_PROVIDER_FOUND') {
        throw new Error("No available providers");
      } else if (result.error.type === 'TRANSFORM_FAILED') {
        throw new Error(`Schema transformation failed: ${result.error.message}`);
      } else if (result.error.type === 'PROVIDER_CALL_FAILED') {
        throw new Error(`Provider call failed: ${result.error.message}`);
      }
      throw new Error(result.error.message);
    }
    
    return {
      data: result.data,
      meta: {
        provider: params.to || "auto-selected", // TODO: Return actual provider
        transformApplied: true,
        latency: Date.now() - startTime
      }
    };
  },
  
  // Test transformation without calling provider
  "contract.test": async (params) => {
    if (!params.dryRun) {
      throw new Error("Only dry run supported in POC");
    }
    
    const forwardResult = await transformer.transform(
      params.testData,
      params.from,
      params.to,
      "forward"
    );
    
    if (!forwardResult.ok) {
      throw new Error(`Forward transformation failed: ${forwardResult.error.message}`);
    }
    
    // Mock response based on schema
    const mockResponse = { temp: 20, humidity: 50, location: forwardResult.data.location || "Unknown" };
    
    const reverseResult = await transformer.transform(
      mockResponse,
      params.to,
      params.from,
      "reverse"
    );
    
    if (!reverseResult.ok) {
      throw new Error(`Reverse transformation failed: ${reverseResult.error.message}`);
    }
    
    return {
      steps: [
        { step: "input", data: params.testData },
        { step: "transformed", data: forwardResult.data },
        { step: "mockResponse", data: mockResponse },
        { step: "output", data: reverseResult.data }
      ]
    };
  }
};

// Handle JSON-RPC2 request
async function handleRpcRequest(request: any): Promise<any> {
  // Validate request
  if (!request.jsonrpc || request.jsonrpc !== "2.0") {
    return {
      jsonrpc: "2.0",
      error: RPC_ERRORS.INVALID_REQUEST,
      id: request.id || null
    };
  }
  
  if (!request.method || typeof request.method !== "string") {
    return {
      jsonrpc: "2.0",
      error: RPC_ERRORS.INVALID_REQUEST,
      id: request.id || null
    };
  }
  
  // Find method
  const method = methods[request.method];
  if (!method) {
    return {
      jsonrpc: "2.0",
      error: RPC_ERRORS.METHOD_NOT_FOUND,
      id: request.id || null
    };
  }
  
  try {
    const result = await method(request.params || {});
    return {
      jsonrpc: "2.0",
      result,
      id: request.id || null
    };
  } catch (error) {
    log("ERROR", {
      uri: "contract.main.handleRpcRequest",
      message: "RPC request failed",
      error: error instanceof Error ? error.message : String(error),
      method: request.method
    });
    
    // Map errors to RPC codes
    if (error instanceof Error) {
      if (error.message.includes("Invalid schema format")) {
        return {
          jsonrpc: "2.0",
          error: {
            ...RPC_ERRORS.INTERNAL_ERROR,
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message === "No available providers") {
        return {
          jsonrpc: "2.0",
          error: {
            ...RPC_ERRORS.NO_PROVIDER,
            data: { consumer: request.params?.from }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Schema transformation failed") || error.message.includes("transformation failed")) {
        return {
          jsonrpc: "2.0",
          error: {
            ...RPC_ERRORS.SCHEMA_MISMATCH,
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Missing required parameter") || error.message.includes("Invalid parameter type")) {
        return {
          jsonrpc: "2.0",
          error: {
            code: -32602,
            message: "Invalid params",
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Schema file not found")) {
        return {
          jsonrpc: "2.0",
          error: {
            code: -32603,
            message: "Internal error",
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Invalid JSON")) {
        return {
          jsonrpc: "2.0",
          error: {
            code: -32603,
            message: "Internal error",
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Invalid JSON Schema")) {
        return {
          jsonrpc: "2.0",
          error: {
            code: -32603,
            message: "Internal error",
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
      
      if (error.message.includes("Invalid registration type")) {
        return {
          jsonrpc: "2.0",
          error: {
            code: -32602,
            message: "Invalid params",
            data: { detail: error.message }
          },
          id: request.id || null
        };
      }
    }
    
    return {
      jsonrpc: "2.0",
      error: RPC_ERRORS.INTERNAL_ERROR,
      id: request.id || null
    };
  }
}

// Server handler function
export async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  
  // JSON-RPC2 endpoint
  if (url.pathname === "/rpc" && req.method === "POST") {
    let body;
    try {
      body = await req.json();
    } catch {
      return Response.json({
        jsonrpc: "2.0",
        error: RPC_ERRORS.PARSE_ERROR,
        id: null
      });
    }
    
    // Handle batch requests
    if (Array.isArray(body)) {
      const responses = await Promise.all(
        body.map(request => handleRpcRequest(request))
      );
      return Response.json(responses);
    }
    
    // Handle single request
    const response = await handleRpcRequest(body);
    return Response.json(response);
  }
  
  return new Response("Not Found", { status: 404 });
}

// Start server if run directly
if (import.meta.main) {
  log("INFO", {
    uri: "contract.main",
    message: "Contract Service starting",
    url: "http://localhost:8000"
  });
  serve(handler, { port: 8000 });
}