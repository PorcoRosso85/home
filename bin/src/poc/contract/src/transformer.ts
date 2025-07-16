// Data Transformer - Handles schema transformations
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
  
  async transform(data: any, from: string, to: string, direction: "forward" | "reverse" = "forward") {
    const key = `${from}->${to}`;
    const transform = this.transforms.get(key);
    
    if (!transform) {
      // Use default mapping
      return this.defaultTransform(data, direction);
    }
    
    const script = direction === "forward" ? transform.forward : transform.reverse;
    if (!script) {
      return this.defaultTransform(data, direction);
    }
    
    // Execute in Worker for isolation
    return await this.executeInWorker(script, data);
  }
  
  private async executeInWorker(script: string, data: any): Promise<any> {
    const workerCode = `
      ${script}
      self.onmessage = (e) => {
        try {
          const result = transform(e.data);
          self.postMessage({ success: true, result });
        } catch (error) {
          self.postMessage({ success: false, error: error.message });
        }
      };
    `;
    
    const blob = new Blob([workerCode], { type: "application/javascript" });
    const worker = new Worker(URL.createObjectURL(blob), {
      type: "module",
      // @ts-ignore - Deno specific
      deno: {
        permissions: "none"  // No permissions - complete isolation
      }
    });
    
    return new Promise((resolve, reject) => {
      worker.onmessage = (e) => {
        worker.terminate();
        if (e.data.success) {
          resolve(e.data.result);
        } else {
          reject(new Error(e.data.error));
        }
      };
      
      worker.onerror = (error) => {
        worker.terminate();
        reject(error);
      };
      
      worker.postMessage(data);
    });
  }
  
  private defaultTransform(data: any, direction: "forward" | "reverse") {
    // Simple field mapping
    const mappings = {
      forward: {
        "city": "location",
        "search_text": "query",
        "max_results": "limit"
      },
      reverse: {
        "temperature": "temp",
        "humidity": "humid", 
        "location": "city"
      }
    };
    
    const mapping = mappings[direction];
    const result: any = {};
    
    for (const [from, to] of Object.entries(mapping)) {
      if (data[from] !== undefined) {
        result[to] = data[from];
      } else if (data[to] !== undefined && direction === "forward") {
        // Keep original field if no mapping
        result[to] = data[to];
      }
    }
    
    // Copy unmapped fields
    for (const [key, value] of Object.entries(data)) {
      if (!result[key] && !(key in mapping)) {
        result[key] = value;
      }
    }
    
    // Handle special accuracy field for high accuracy providers
    if (result.accuracy === "high") {
      result.accuracy = "high";
    }
    
    return result;
  }
}