// Test helpers for clean resource management
import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createCausalSyncClient, disconnect } from "./causal-sync-client.ts";

interface TestResource {
  cleanup: () => Promise<void> | void;
}

export class TestResourceManager {
  private resources: TestResource[] = [];
  private cleanupPromises: Promise<void>[] = [];
  
  register(resource: TestResource): void {
    this.resources.push(resource);
  }
  
  async cleanupAll(): Promise<void> {
    // Reverse order cleanup (LIFO)
    const reversed = [...this.resources].reverse();
    
    for (const resource of reversed) {
      try {
        const result = resource.cleanup();
        if (result instanceof Promise) {
          this.cleanupPromises.push(result);
        }
      } catch (error) {
        console.error("Cleanup error:", error);
      }
    }
    
    // Wait for all async cleanups
    await Promise.allSettled(this.cleanupPromises);
    
    // Clear resources
    this.resources = [];
    this.cleanupPromises = [];
  }
}

export interface TestContext {
  tempDir: string;
  wsPort: number;
  wsUrl: string;
  serverProcess?: Deno.ChildProcess;
  resourceManager: TestResourceManager;
  clients: Map<string, any>;
}

// Generate unique port for each test
let portCounter = 8090;
function getUniquePort(): number {
  return portCounter++;
}

// Create isolated test context
export async function createTestContext(): Promise<TestContext> {
  const tempDir = await Deno.makeTempDir({ prefix: "kuzu_test_" });
  const wsPort = getUniquePort();
  const wsUrl = `ws://localhost:${wsPort}`;
  const resourceManager = new TestResourceManager();
  
  // Register temp dir cleanup
  resourceManager.register({
    cleanup: async () => {
      try {
        await Deno.remove(tempDir, { recursive: true });
      } catch {
        // Ignore if already removed
      }
    }
  });
  
  return {
    tempDir,
    wsPort,
    wsUrl,
    resourceManager,
    clients: new Map()
  };
}

// Start WebSocket server in isolated context
export async function startTestServer(ctx: TestContext): Promise<void> {
  // Start server process with unique port
  const command = new Deno.Command("deno", {
    args: [
      "run",
      "--allow-net",
      "--no-check",
      new URL("./websocket-server-isolated.ts", import.meta.url).pathname
    ],
    env: { PORT: ctx.wsPort.toString() },
    stdout: "piped",
    stderr: "piped"
  });
  
  ctx.serverProcess = command.spawn();
  
  // Register server cleanup
  ctx.resourceManager.register({
    cleanup: async () => {
      if (ctx.serverProcess) {
        try {
          ctx.serverProcess.kill();
          await ctx.serverProcess.status;
        } catch {
          // Process may already be terminated
        }
      }
    }
  });
  
  // Wait for server to start
  console.log(`Starting WebSocket server on port ${ctx.wsPort}...`);
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Verify server is running
  try {
    const ws = new WebSocket(ctx.wsUrl);
    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => {
        ws.close();
        resolve();
      };
      ws.onerror = () => reject(new Error("Server not started"));
      setTimeout(() => reject(new Error("Server start timeout")), 3000);
    });
    console.log(`WebSocket server started successfully on port ${ctx.wsPort}`);
  } catch (error) {
    console.error(`Failed to start server on port ${ctx.wsPort}:`, error);
    throw error;
  }
}

// Create test client with automatic cleanup
export async function createManagedTestClient(
  ctx: TestContext,
  clientId: string
): Promise<any> {
  const client = await createCausalSyncClient({
    clientId,
    dbPath: `:memory:`,
    wsUrl: ctx.wsUrl
  });
  
  ctx.clients.set(clientId, client);
  
  // Register client cleanup
  ctx.resourceManager.register({
    cleanup: async () => {
      try {
        await disconnect(client);
      } catch {
        // Client may already be disconnected
      }
    }
  });
  
  return client;
}

// Test wrapper with automatic cleanup
export async function withTestContext(
  testFn: (ctx: TestContext) => Promise<void>
): Promise<void> {
  const ctx = await createTestContext();
  
  try {
    await startTestServer(ctx);
    await testFn(ctx);
  } finally {
    await ctx.resourceManager.cleanupAll();
  }
}

// Helper to wait for all pending operations
export async function waitForPendingOperations(
  client: any,
  timeout: number = 5000
): Promise<void> {
  const start = Date.now();
  
  while (Date.now() - start < timeout) {
    const internal = client._internal;
    if (internal && internal.pendingOperations.size === 0) {
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}

// Graceful shutdown helper
export async function gracefulShutdown(ctx: TestContext): Promise<void> {
  // 1. Close all client connections gracefully
  for (const [clientId, client] of ctx.clients) {
    try {
      await waitForPendingOperations(client);
      await disconnect(client);
    } catch (error) {
      console.error(`Error disconnecting client ${clientId}:`, error);
    }
  }
  
  // 2. Wait a bit for final messages
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // 3. Stop server
  if (ctx.serverProcess) {
    ctx.serverProcess.kill();
    await ctx.serverProcess.status;
  }
  
  // 4. Final cleanup
  await ctx.resourceManager.cleanupAll();
}