// Contract Matcher - Finds compatible services
import { Database } from "./kuzu_wrapper.ts";

export class Matcher {
  constructor(private db: Database) {}
  
  async findContracts(consumerUri: string) {
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})-[r:CAN_CALL]->(p:Provider)
      RETURN p.uri as provider, r.transform as transform, p.endpoint as endpoint
    `, { uri: consumerUri });
    
    const canCall = result.map((row: any) => ({
      provider: row.provider,
      transform: row.transform,
      endpoint: row.endpoint
    }));
    
    return { 
      consumer: consumerUri,
      canCall 
    };
  }
  
  async findBestProvider(consumerUri: string, preferences?: any) {
    // If preferences specify accuracy, filter providers
    if (preferences?.accuracy === "high") {
      const result = await this.db.query(`
        MATCH (c:Consumer {uri: $uri})-[:CAN_CALL]->(p:Provider)
        WHERE p.metadata CONTAINS '"accuracy":"high"'
        RETURN p.uri as provider, p.endpoint as endpoint
        LIMIT 1
      `, { uri: consumerUri });
      
      if (result.length > 0) {
        return result[0];
      }
    }
    
    // Default: return first available provider
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})-[:CAN_CALL]->(p:Provider)
      RETURN p.uri as provider, p.endpoint as endpoint
      LIMIT 1
    `, { uri: consumerUri });
    
    if (result.length === 0) {
      throw new Error("No available providers");
    }
    
    return result[0];
  }
  
  async findConsumersFor(providerUri: string) {
    // Find all consumers that can use this provider
    const result = await this.db.query(`
      MATCH (p:Provider {uri: $uri})<-[:CAN_CALL]-(c:Consumer)
      RETURN c.uri as consumer
    `, {
      uri: providerUri
    });
    
    return result.map(r => ({
      consumer: r.consumer
    }));
  }
  
  async findProvidersFor(consumerUri: string) {
    // Find all providers this consumer can call
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})-[:CAN_CALL]->(p:Provider)
      RETURN p.uri as provider, p.endpoint as endpoint
    `, {
      uri: consumerUri
    });
    
    return result.map(r => ({
      provider: r.provider,
      endpoint: r.endpoint
    }));
  }
}