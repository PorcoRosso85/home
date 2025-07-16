// Contract Registry - Manages provider and consumer registrations
import { Database } from "./kuzu_wrapper.ts";

export interface ProviderRegistration {
  uri: string;
  schema: {
    input?: any;
    output?: any;
  };
  endpoint?: string;
  metadata?: any;
}

export interface ConsumerRegistration {
  uri: string;
  expects: {
    input?: any;
    output?: any;
  };
}

export class Registry {
  constructor(private db: Database) {}
  
  async registerProvider(data: ProviderRegistration) {
    // Validate schema
    if (!data.schema || typeof data.schema !== "object") {
      throw new Error("Invalid schema format");
    }
    
    // Store in graph DB
    await this.db.query(`
      MERGE (p:Provider {uri: $uri})
      SET p.endpoint = $endpoint,
          p.metadata = $metadata
      WITH p
      MERGE (s:Schema {
        input: $input,
        output: $output,
        hash: $hash
      })
      MERGE (p)-[:PROVIDES]->(s)
    `, {
      uri: data.uri,
      endpoint: data.endpoint || null,
      metadata: JSON.stringify(data.metadata || {}),
      input: JSON.stringify(data.schema.input || {}),
      output: JSON.stringify(data.schema.output || {}),
      hash: this.hashSchema(data.schema)
    });
    
    return {
      status: "registered",
      provider: data.uri
    };
  }
  
  async registerConsumer(data: ConsumerRegistration) {
    // Validate schema
    if (!data.expects || typeof data.expects !== "object") {
      throw new Error("Invalid schema format");
    }
    
    // Store in graph DB
    await this.db.query(`
      MERGE (c:Consumer {uri: $uri})
      WITH c
      MERGE (s:Schema {
        input: $input,
        output: $output,
        hash: $hash
      })
      MERGE (c)-[:EXPECTS]->(s)
    `, {
      uri: data.uri,
      input: JSON.stringify(data.expects.input || {}),
      output: JSON.stringify(data.expects.output || {}),
      hash: this.hashSchema(data.expects)
    });
    
    // Trigger matching for new consumer
    await this.findAndCreateMatches(data.uri);
    
    return {
      status: "registered",
      consumer: data.uri
    };
  }
  
  private async findAndCreateMatches(consumerUri: string) {
    // Find compatible providers - simplified for MVP
    // In real implementation, match based on schema compatibility
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})
      MATCH (p:Provider)
      MERGE (c)-[r:CAN_CALL]->(p)
      SET r.transform = $defaultTransform
      RETURN p.uri as provider
    `, {
      uri: consumerUri,
      defaultTransform: JSON.stringify(this.generateDefaultTransform())
    });
    
    return result;
  }
  
  private hashSchema(schema: any): string {
    return JSON.stringify(schema); // Simple hash for now
  }
  
  private generateDefaultTransform() {
    // Simple field mapping for now
    return {
      output: {
        "location": "city",
        "city": "location"
      },
      input: {
        "temperature": "temp",
        "humidity": "humid",
        "location": "city",
        "temp": "temperature",
        "humid": "humidity",
        "city": "location"
      }
    };
  }
}