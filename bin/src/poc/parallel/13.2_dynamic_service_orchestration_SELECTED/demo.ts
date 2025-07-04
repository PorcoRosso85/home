// POC 13.2 Demo: Dynamic Service Orchestration
import { ServiceOrchestrator } from "./service-orchestrator.ts";

console.log("🚀 POC 13.2: Dynamic Service Orchestration Demo");
console.log("=============================================");
console.log("");

// Create orchestrator with fast intervals for demo
const orchestrator = new ServiceOrchestrator({
  discoveryInterval: 2000,    // Check for new services every 2s
  healthCheckInterval: 3000   // Health check every 3s
});

// Initial services
console.log("📦 Registering initial services...");
await orchestrator.register({
  id: "app-1",
  name: "app",
  host: "localhost",
  port: 4001,
  metadata: { version: "1.0.0", region: "us-east" }
});

await orchestrator.register({
  id: "app-2",
  name: "app",
  host: "localhost",
  port: 4002,
  metadata: { version: "1.0.0", region: "eu-west" }
});

console.log("✅ Initial services registered");

// Show initial state
const initialServices = await orchestrator.discover("app");
console.log(`\n📊 Current services: ${initialServices.length}`);
initialServices.forEach(s => {
  console.log(`   - ${s.id} at ${s.host}:${s.port} (${s.metadata?.region})`);
});

// Simulate routing
console.log("\n🔄 Testing routing (5 requests):");
for (let i = 0; i < 5; i++) {
  const selected = await orchestrator.route({ path: "/" });
  console.log(`   Request ${i + 1} → ${selected.id}`);
}

// Simulate new container joining
console.log("\n📦 New container joining in 3 seconds...");
setTimeout(async () => {
  await orchestrator.register({
    id: "app-3",
    name: "app",
    host: "localhost",
    port: 4003,
    metadata: { version: "1.0.0", region: "us-east" }
  });
  console.log("✅ app-3 joined the cluster!");
}, 3000);

// Simulate container failure
console.log("💥 Simulating app-2 failure in 6 seconds...");
setTimeout(() => {
  orchestrator.healthChecker.mockHealthStatus("app-2", "unhealthy");
  console.log("❌ app-2 marked as unhealthy");
}, 6000);

// Monitor changes
setTimeout(async () => {
  console.log("\n📊 Final state after changes:");
  const finalServices = await orchestrator.discover("app");
  console.log(`   Total registered: ${finalServices.length}`);
  
  const healthy = await orchestrator.healthChecker.getHealthyServices(finalServices);
  console.log(`   Healthy services: ${healthy.length}`);
  healthy.forEach(s => {
    console.log(`   - ${s.id} ✅`);
  });
  
  console.log("\n🔄 Testing routing after changes:");
  const routingTest = new Map<string, number>();
  for (let i = 0; i < 10; i++) {
    const selected = await orchestrator.route({ path: "/" });
    routingTest.set(selected.id, (routingTest.get(selected.id) || 0) + 1);
  }
  
  console.log("   Distribution:");
  for (const [id, count] of routingTest) {
    console.log(`   - ${id}: ${count} requests`);
  }
  
  // Canary deployment demo
  console.log("\n🐤 Testing canary deployment (v2.0.0 at 20%):");
  await orchestrator.deployment.canaryDeploy({
    id: "app-v2",
    name: "app",
    host: "localhost",
    port: 4004,
    metadata: { version: "2.0.0" }
  }, 20);
  
  const versionCount = { v1: 0, v2: 0 };
  for (let i = 0; i < 50; i++) {
    const selected = await orchestrator.route({ path: "/" });
    if (selected.metadata?.version === "2.0.0") {
      versionCount.v2++;
    } else {
      versionCount.v1++;
    }
  }
  
  console.log(`   v1.0.0: ${versionCount.v1} requests (${(versionCount.v1/50*100).toFixed(0)}%)`);
  console.log(`   v2.0.0: ${versionCount.v2} requests (${(versionCount.v2/50*100).toFixed(0)}%)`);
  
  console.log("\n✅ Demo completed!");
  console.log("Key features demonstrated:");
  console.log("- ✅ Automatic service discovery");
  console.log("- ✅ Dynamic container joining");
  console.log("- ✅ Automatic unhealthy service exclusion");
  console.log("- ✅ Canary deployment");
  
  // Cleanup
  orchestrator.destroy();
  Deno.exit(0);
}, 10000);