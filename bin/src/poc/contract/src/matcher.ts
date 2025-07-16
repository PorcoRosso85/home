// Contract Matcher - Finds compatible services
import { Database } from "./kuzu_wrapper.ts";

export class Matcher {
  constructor(private db: Database) {}
  
  async findContracts(consumerUri: string) {
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})-[r:CAN_CALL]->(p:Provider)
      RETURN p.uri as provider, r.transform as transform
    `, { uri: consumerUri });
    
    const canCall = result.map((row: any) => ({
      provider: row.provider,
      transform: JSON.parse(row.transform || "{}")
    }));
    
    return { canCall };
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
}