import { describe, it, expect } from "vitest";
import handler from "../src/framework/entry.rsc";

describe("RSC Entry Point", () => {
  it("should export a handler function", () => {
    expect(typeof handler).toBe("function");
  });

  it("should return a Response object", async () => {
    const mockRequest = new Request("http://localhost:3000");
    const result = await handler(mockRequest);
    
    expect(result).toBeInstanceOf(Response);
  });

  it("should return HTML content type", async () => {
    const mockRequest = new Request("http://localhost:3000");
    const response = await handler(mockRequest);
    
    expect(response.headers.get("Content-Type")).toBe("text/html");
  });

  it("should return HTML content with expected structure", async () => {
    const mockRequest = new Request("http://localhost:3000");
    const response = await handler(mockRequest);
    const html = await response.text();
    
    expect(html).toContain("<!DOCTYPE html>");
    expect(html).toContain("<title>Vite RSC POC</title>");
    expect(html).toContain("React Server Components POC");
  });

  it("should return status 200", async () => {
    const mockRequest = new Request("http://localhost:3000");
    const response = await handler(mockRequest);
    
    expect(response.status).toBe(200);
  });
});