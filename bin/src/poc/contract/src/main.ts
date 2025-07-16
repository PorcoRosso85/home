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

// Server handler function
export async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const method = req.method;
  
  try {
    // Health check
    if (url.pathname === "/health" && method === "GET") {
      return new Response("OK", { status: 200 });
    }
    
    // Register provider
    if (url.pathname === "/register/provider" && method === "POST") {
      const data = await req.json();
      const result = await registry.registerProvider(data);
      return Response.json(result, { status: 201 });
    }
    
    // Register consumer
    if (url.pathname === "/register/consumer" && method === "POST") {
      const data = await req.json();
      const result = await registry.registerConsumer(data);
      return Response.json(result, { status: 201 });
    }
    
    // Get contracts for a consumer
    if (url.pathname.startsWith("/contracts/") && method === "GET") {
      const consumer = decodeURIComponent(url.pathname.slice(11));
      const contracts = await matcher.findContracts(consumer);
      return Response.json(contracts);
    }
    
    // Register transform
    if (url.pathname === "/transform/register" && method === "POST") {
      const data = await req.json();
      await transformer.registerTransform(data);
      return Response.json({ status: "registered" });
    }
    
    // Call service
    if (url.pathname === "/call" && method === "POST") {
      const data = await req.json();
      const result = await router.call(data);
      return Response.json(result);
    }
    
    return new Response("Not Found", { status: 404 });
    
  } catch (error) {
    console.error("Error:", error);
    
    if (error instanceof Error) {
      if (error.message === "Invalid schema format") {
        return Response.json({ error: error.message }, { status: 400 });
      }
      
      if (error.message === "No available providers") {
        return Response.json({ error: error.message }, { status: 503 });
      }
    }
    
    return Response.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

// Start server if run directly
if (import.meta.main) {
  console.log("Contract Service starting on http://localhost:8000");
  serve(handler, { port: 8000 });
}