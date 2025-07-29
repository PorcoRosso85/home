#!/usr/bin/env -S deno run --allow-net --allow-read

/**
 * Statistics Monitoring Demo
 * Demonstrates the periodic stats reporter output
 */

import { SyncKuzuClient } from "../core/sync_kuzu_client.ts";

// Mock classes to avoid KuzuDB WASM issues
class MockBrowserKuzuClient {
  async initialize(): Promise<void> {}
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<any> {
    return {
      id: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      template,
      params,
      timestamp: Date.now(),
      clientId: "mock-client"
    };
  }
  
  async applyEvent(event: any): Promise<void> {
    // Simulate occasional failures
    if (Math.random() < 0.1) {
      throw new Error("Simulated apply error");
    }
  }
  
  onRemoteEvent(handler: (event: any) => void): void {}
}

class MockSyncClient {
  private clientId: string;
  private eventHandlers: Array<(event: any) => void> = [];
  
  constructor(clientId: string) {
    this.clientId = clientId;
  }
  
  getClientId(): string {
    return this.clientId;
  }
  
  async connect(url: string): Promise<void> {
    console.log(`✅ Connected to ${url} (simulated)`);
  }
  
  async sendEvent(event: any): Promise<void> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Simulate remote events coming back
    setTimeout(() => {
      this.eventHandlers.forEach(handler => handler(event));
    }, 100);
  }
  
  onEvent(handler: (event: any) => void): void {
    this.eventHandlers.push(handler);
  }
  
  async close(): Promise<void> {}
}

async function main() {
  console.log("🚀 Starting Sync KuzuDB Client Statistics Monitoring Demo\n");
  
  const client = new SyncKuzuClient({
    clientId: "stats-demo-client",
    autoReconnect: true,
    reconnectDelay: 2000
  });
  
  // Replace internal clients with mocks
  (client as any).kuzuClient = new MockBrowserKuzuClient();
  (client as any).syncClient = new MockSyncClient("stats-demo-client");
  
  // Re-setup event handler
  (client as any).syncClient.onEvent(async (event: any) => {
    const incrementStats = (client as any).incrementTemplateStats.bind(client);
    incrementStats(event.template, 'received');
    
    try {
      await (client as any).kuzuClient.applyEvent(event);
      (client as any).dmlStats.applied++;
      incrementStats(event.template, 'applied');
    } catch (error) {
      (client as any).dmlStats.failed++;
      incrementStats(event.template, 'failed');
    }
    
    (client as any).dmlStats.received++;
  });
  
  try {
    console.log("📊 Statistics will be logged every 5 seconds...\n");
    console.log("=" .repeat(60));
    
    // Connect to mock server
    await client.connect("ws://localhost:8080");
    
    // Simulate various DML operations
    const templates = [
      { name: "CREATE_USER", weight: 4 },
      { name: "UPDATE_USER", weight: 3 },
      { name: "DELETE_USER_DATA", weight: 1 },
      { name: "INCREMENT_COUNTER", weight: 2 },
      { name: "CREATE_POST", weight: 2 },
      { name: "FOLLOW_USER", weight: 1 }
    ];
    
    let operationCount = 0;
    const totalOperations = 20;
    
    // Execute operations over time
    const interval = setInterval(async () => {
      if (operationCount >= totalOperations) {
        clearInterval(interval);
        
        console.log("\n⏳ All operations completed. Waiting for final stats...");
        await new Promise(resolve => setTimeout(resolve, 7000));
        
        // Get and display final detailed stats
        console.log("\n" + "=".repeat(60));
        console.log("📈 Final Detailed Statistics by Template:");
        console.log("=".repeat(60));
        
        const detailedStats = client.getDetailedStatsByTemplate();
        
        for (const [template, stats] of Object.entries(detailedStats)) {
          console.log(`\n📌 ${template}:`);
          console.log(`   Sent:         ${stats.sent}`);
          console.log(`   Received:     ${stats.received}`);
          console.log(`   Applied:      ${stats.applied}`);
          console.log(`   Failed:       ${stats.failed}`);
          console.log(`   Success Rate: ${stats.successRate.toFixed(2)}%`);
        }
        
        // Get overall stats
        const overallStats = client.getDMLStats();
        console.log("\n" + "=".repeat(60));
        console.log("📊 Overall Statistics:");
        console.log("=".repeat(60));
        console.log(`   Client ID:      ${overallStats.clientId}`);
        console.log(`   Total Sent:     ${overallStats.sent}`);
        console.log(`   Total Received: ${overallStats.received}`);
        console.log(`   Total Applied:  ${overallStats.applied}`);
        console.log(`   Total Failed:   ${overallStats.failed}`);
        
        const successRate = overallStats.applied > 0 || overallStats.failed > 0
          ? (overallStats.applied / (overallStats.applied + overallStats.failed)) * 100
          : 0;
        console.log(`   Success Rate:   ${successRate.toFixed(2)}%`);
        
        await client.close();
        console.log("\n✅ Demo completed!");
        return;
      }
      
      // Pick a random template based on weights
      const totalWeight = templates.reduce((sum, t) => sum + t.weight, 0);
      let random = Math.random() * totalWeight;
      let selectedTemplate = templates[0].name;
      
      for (const template of templates) {
        random -= template.weight;
        if (random <= 0) {
          selectedTemplate = template.name;
          break;
        }
      }
      
      // Generate appropriate params
      const params = generateParams(selectedTemplate, operationCount);
      
      console.log(`\n⚡ [${operationCount + 1}/${totalOperations}] Executing: ${selectedTemplate}`);
      
      try {
        await client.executeTemplate(selectedTemplate, params);
        console.log(`   ✅ Success`);
      } catch (error) {
        console.error(`   ❌ Failed: ${error.message}`);
      }
      
      operationCount++;
    }, 1500); // Execute operation every 1.5 seconds
    
  } catch (error) {
    console.error("❌ Error:", error);
    await client.close();
  }
}

function generateParams(template: string, index: number): Record<string, any> {
  switch (template) {
    case "CREATE_USER":
      return {
        id: `user_${index}`,
        name: `User ${index}`,
        email: `user${index}@example.com`
      };
    case "UPDATE_USER":
      return {
        id: `user_${Math.floor(Math.random() * index)}`,
        name: `Updated User ${Date.now()}`
      };
    case "DELETE_USER_DATA":
      return {
        userId: `user_${Math.floor(Math.random() * index)}`,
        reason: "GDPR request"
      };
    case "INCREMENT_COUNTER":
      return {
        counterId: `counter_${Math.floor(Math.random() * 3)}`,
        amount: Math.floor(Math.random() * 10) + 1
      };
    case "CREATE_POST":
      return {
        id: `post_${index}`,
        content: `Post content ${index}`,
        authorId: `user_${Math.floor(Math.random() * index)}`
      };
    case "FOLLOW_USER":
      return {
        followerId: `user_${Math.floor(Math.random() * index)}`,
        targetId: `user_${Math.floor(Math.random() * index)}`
      };
    default:
      return { id: `item_${index}` };
  }
}

// Run the demo
if (import.meta.main) {
  await main();
}