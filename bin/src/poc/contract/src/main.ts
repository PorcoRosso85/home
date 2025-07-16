// Contract Service - Main Entry Point
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { Router } from "./router.ts";
import { Registry } from "./registry.ts";
import { Matcher } from "./matcher.ts";
import { Transformer } from "./transformer.ts";
import { initDatabase } from "./kuzu_wrapper.ts";

// Initialize components
const db = await initDatabase();
const registry = new Registry(db);
const matcher = new Matcher(db);
const transformer = new Transformer();
const router = new Router(registry, matcher, transformer);

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
    if (params.type === "provider") {
      const result = await registry.registerProvider({
        uri: params.uri,
        schema: params.schema,
        endpoint: params.endpoint,
        metadata: params.metadata
      });
      
      // Find matching consumers
      const matches = await matcher.findConsumersFor(params.uri);
      return {
        ...result,
        matches: matches.map(m => ({
          consumer: m.consumer,
          compatibility: 0.9, // TODO: Calculate real compatibility
          autoTransform: true
        }))
      };
    } else if (params.type === "consumer") {
      const result = await registry.registerConsumer({
        uri: params.uri,
        expects: params.expects
      });
      
      // Find available providers
      const providers = await matcher.findProvidersFor(params.uri);
      return {
        ...result,
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
    throw new Error("Invalid registration type");
  },
  
  // Call a service with automatic transformation
  "contract.call": async (params) => {
    const startTime = Date.now();
    const result = await router.call({
      from: params.from,
      data: params.data,
      preferences: params.preferences
    });
    
    return {
      data: result,
      meta: {
        provider: params.to || "auto-selected", // TODO: Return actual provider
        transformApplied: true,
        latency: Date.now() - startTime
      }
    };
  },
  
  // Inspect transformation rules
  "contract.inspect": async (params) => {
    const contracts = await matcher.findContracts(params.consumer);
    const contract = contracts.canCall.find(c => c.provider === params.provider);
    
    if (!contract) {
      return {
        compatible: false,
        transform: null,
        confidence: 0,
        issues: ["No matching contract found"]
      };
    }
    
    return {
      compatible: true,
      transform: JSON.parse(contract.transform || "{}"),
      confidence: 0.9,
      issues: []
    };
  },
  
  // Test transformation without calling provider
  "contract.test": async (params) => {
    if (!params.dryRun) {
      throw new Error("Only dry run supported in POC");
    }
    
    const forward = await transformer.transform(
      params.testData,
      params.from,
      params.to,
      "forward"
    );
    
    // Mock response based on schema
    const mockResponse = { temp: 20, humidity: 50, location: forward.location || "Unknown" };
    
    const reverse = await transformer.transform(
      mockResponse,
      params.to,
      params.from,
      "reverse"
    );
    
    return {
      steps: [
        { step: "input", data: params.testData },
        { step: "transformed", data: forward },
        { step: "mockResponse", data: mockResponse },
        { step: "output", data: reverse }
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
    console.error("RPC Error:", error);
    
    // Map errors to RPC codes
    if (error instanceof Error) {
      if (error.message === "Invalid schema format") {
        return {
          jsonrpc: "2.0",
          error: {
            ...RPC_ERRORS.INVALID_SCHEMA,
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
  
  // Health check
  if (url.pathname === "/health" && req.method === "GET") {
    return new Response("OK", { status: 200 });
  }
  
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
  console.log("Contract Service starting on http://localhost:8000");
  serve(handler, { port: 8000 });
}