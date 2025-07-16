// Service Router - Routes calls through the contract service
import { Registry } from "./registry.ts";
import { Matcher } from "./matcher.ts";
import { Transformer } from "./transformer.ts";

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
  }) {
    // Find best matching provider
    const provider = await this.matcher.findBestProvider(request.from, request.preferences);
    
    if (!provider || !provider.endpoint) {
      throw new Error("No available providers");
    }
    
    // Transform request data
    const transformedData = await this.transformer.transform(
      request.data,
      request.from,
      provider.provider,
      "forward"
    );
    
    // Call actual provider
    let response;
    try {
      const result = await fetch(provider.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(transformedData)
      });
      
      if (!result.ok) {
        throw new Error(`Provider returned ${result.status}`);
      }
      
      response = await result.json();
    } catch (error) {
      console.error("Provider call failed:", error);
      throw new Error("No available providers");
    }
    
    // Transform response back
    const transformedResponse = await this.transformer.transform(
      response,
      provider.provider,
      request.from,
      "reverse"
    );
    
    return transformedResponse;
  }
}