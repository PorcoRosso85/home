// Types
export interface ServerInfo {
  id: string;
  host: string;
  port: number;
  url: string;
  healthy: boolean;
  connections: number;
}

export interface HealthStatus {
  serverId: string;
  healthy: boolean;
  responseTime: number;
  error?: string;
}

export interface LoadBalancer {
  selectServer(): ServerInfo;
  getServerCount(): number;
  addServer(server: ServerInfo): void;
  removeServer(serverId: string): void;
}

// Parse server list from environment variable format
export function parseServers(serversStr: string): ServerInfo[] {
  if (!serversStr || serversStr.trim() === "") {
    throw new Error("BACKEND_SERVERS cannot be empty");
  }
  
  return serversStr.split(",").map((serverStr, index) => {
    const [host, portStr] = serverStr.trim().split(":");
    const port = parseInt(portStr);
    
    if (!host || isNaN(port)) {
      throw new Error(`Invalid server format: ${serverStr}`);
    }
    
    return {
      id: `server-${index + 1}`,
      host,
      port,
      url: `http://${host}:${port}`,
      healthy: true,
      connections: 0
    };
  });
}

// Load balancer factory
export function createLoadBalancer(
  servers: ServerInfo[], 
  strategy: "round-robin" | "random" | "least-conn"
): LoadBalancer {
  switch (strategy) {
    case "round-robin":
      return new RoundRobinBalancer(servers);
    case "random":
      return new RandomBalancer(servers);
    case "least-conn":
      return new LeastConnectionsBalancer(servers);
    default:
      throw new Error(`Unknown strategy: ${strategy}`);
  }
}

// Round Robin implementation
class RoundRobinBalancer implements LoadBalancer {
  private servers: ServerInfo[];
  private currentIndex = 0;
  
  constructor(servers: ServerInfo[]) {
    this.servers = [...servers];
  }
  
  selectServer(): ServerInfo {
    const healthyServers = this.servers.filter(s => s.healthy);
    
    if (healthyServers.length === 0) {
      throw new Error("No healthy servers available");
    }
    
    // Find next healthy server starting from currentIndex
    let attempts = 0;
    while (attempts < this.servers.length) {
      const server = this.servers[this.currentIndex];
      this.currentIndex = (this.currentIndex + 1) % this.servers.length;
      
      if (server.healthy) {
        return server;
      }
      attempts++;
    }
    
    throw new Error("No healthy servers available");
  }
  
  getServerCount(): number {
    return this.servers.length;
  }
  
  addServer(server: ServerInfo): void {
    this.servers.push(server);
  }
  
  removeServer(serverId: string): void {
    this.servers = this.servers.filter(s => s.id !== serverId);
  }
}

// Random balancer implementation
class RandomBalancer implements LoadBalancer {
  private servers: ServerInfo[];
  
  constructor(servers: ServerInfo[]) {
    this.servers = [...servers];
  }
  
  selectServer(): ServerInfo {
    const healthyServers = this.servers.filter(s => s.healthy);
    
    if (healthyServers.length === 0) {
      throw new Error("No healthy servers available");
    }
    
    const randomIndex = Math.floor(Math.random() * healthyServers.length);
    return healthyServers[randomIndex];
  }
  
  getServerCount(): number {
    return this.servers.length;
  }
  
  addServer(server: ServerInfo): void {
    this.servers.push(server);
  }
  
  removeServer(serverId: string): void {
    this.servers = this.servers.filter(s => s.id !== serverId);
  }
}

// Least Connections balancer implementation
class LeastConnectionsBalancer implements LoadBalancer {
  private servers: ServerInfo[];
  private roundRobinIndex = 0;
  
  constructor(servers: ServerInfo[]) {
    this.servers = [...servers];
  }
  
  selectServer(): ServerInfo {
    const healthyServers = this.servers.filter(s => s.healthy);
    
    if (healthyServers.length === 0) {
      throw new Error("No healthy servers available");
    }
    
    // Sort by connections (ascending)
    const sortedServers = [...healthyServers].sort((a, b) => a.connections - b.connections);
    
    // Get all servers with minimum connections
    const minConnections = sortedServers[0].connections;
    const serversWithMinConnections = sortedServers.filter(s => s.connections === minConnections);
    
    // If multiple servers have same connections, use round-robin among them
    if (serversWithMinConnections.length > 1) {
      const selected = serversWithMinConnections[this.roundRobinIndex % serversWithMinConnections.length];
      this.roundRobinIndex++;
      return selected;
    }
    
    return serversWithMinConnections[0];
  }
  
  getServerCount(): number {
    return this.servers.length;
  }
  
  addServer(server: ServerInfo): void {
    this.servers.push(server);
  }
  
  removeServer(serverId: string): void {
    this.servers = this.servers.filter(s => s.id !== serverId);
  }
}

// Health check function
export async function checkAllServers(servers: ServerInfo[]): Promise<HealthStatus[]> {
  const healthChecks = servers.map(async (server) => {
    const startTime = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
      
      const response = await fetch(`${server.url}/health`, {
        signal: controller.signal,
        method: "GET"
      });
      
      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;
      
      return {
        serverId: server.id,
        healthy: response.ok,
        responseTime,
        error: response.ok ? undefined : `HTTP ${response.status}`
      };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        serverId: server.id,
        healthy: false,
        responseTime,
        error: error instanceof Error ? error.message : "Unknown error"
      };
    }
  });
  
  return Promise.all(healthChecks);
}

// Main proxy server implementation
export async function startEnvoyProxy(config: {
  backendServers: string;
  strategy: "round-robin" | "random" | "least-conn";
  port: number;
  adminPort: number;
}) {
  const servers = parseServers(config.backendServers);
  const loadBalancer = createLoadBalancer(servers, config.strategy);
  
  console.log(`🔄 Envoy Proxy (N-servers) starting...`);
  console.log(`📊 Strategy: ${config.strategy}`);
  console.log(`🖥️  Backends: ${servers.length} servers`);
  servers.forEach(s => console.log(`   - ${s.id}: ${s.url}`));
  
  // Health check interval
  setInterval(async () => {
    const healthStatuses = await checkAllServers(servers);
    
    // Update server health status
    healthStatuses.forEach(status => {
      const server = servers.find(s => s.id === status.serverId);
      if (server) {
        server.healthy = status.healthy;
      }
    });
    
    const healthyCount = servers.filter(s => s.healthy).length;
    console.log(`❤️  Health check: ${healthyCount}/${servers.length} healthy`);
  }, 10000); // Every 10s
  
  // Request tracking
  const stats = {
    total: 0,
    perServer: {} as Record<string, number>,
    errors: 0
  };
  
  // Initialize per-server stats
  servers.forEach(s => stats.perServer[s.id] = 0);
  
  // Main proxy server
  const server = Deno.serve({ port: config.port }, async (request) => {
    const url = new URL(request.url);
    stats.total++;
    
    try {
      const backend = loadBalancer.selectServer();
      const targetUrl = `${backend.url}${url.pathname}${url.search}`;
      
      // Track connections for least-conn strategy
      backend.connections++;
      
      // Forward request
      const backendResponse = await fetch(targetUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body
      });
      
      // Update stats
      stats.perServer[backend.id]++;
      
      // Decrease connections after response
      backend.connections--;
      
      // Add proxy headers
      const responseHeaders = new Headers(backendResponse.headers);
      responseHeaders.set("x-envoy-upstream-service", backend.id);
      
      return new Response(backendResponse.body, {
        status: backendResponse.status,
        headers: responseHeaders
      });
      
    } catch (error) {
      stats.errors++;
      return new Response(JSON.stringify({
        error: "Proxy error",
        details: error instanceof Error ? error.message : "Unknown error"
      }), {
        status: 503,
        headers: { "content-type": "application/json" }
      });
    }
  });
  
  // Admin interface
  const adminServer = Deno.serve({ port: config.adminPort }, (request) => {
    const url = new URL(request.url);
    
    if (url.pathname === "/stats") {
      const distribution = Object.entries(stats.perServer).map(([id, count]) => ({
        server: id,
        requests: count,
        percentage: stats.total > 0 ? ((count / stats.total) * 100).toFixed(1) + "%" : "0%"
      }));
      
      return new Response(JSON.stringify({
        uptime: Math.floor(performance.now() / 1000),
        totalRequests: stats.total,
        errors: stats.errors,
        servers: servers.map(s => ({
          id: s.id,
          healthy: s.healthy,
          connections: s.connections,
          url: s.url
        })),
        distribution
      }, null, 2), {
        headers: { "content-type": "application/json" }
      });
    }
    
    if (url.pathname === "/health") {
      const healthyCount = servers.filter(s => s.healthy).length;
      return new Response(JSON.stringify({
        status: healthyCount > 0 ? "healthy" : "unhealthy",
        healthyServers: healthyCount,
        totalServers: servers.length
      }), {
        headers: { "content-type": "application/json" }
      });
    }
    
    return new Response(`Envoy Admin Interface

Endpoints:
  /stats  - View detailed statistics
  /health - Health status
  
Current Status:
  Strategy: ${config.strategy}
  Servers: ${servers.length}
  Healthy: ${servers.filter(s => s.healthy).length}
`);
  });
  
  return { server, adminServer };
}

// CLI entry point
if (import.meta.main) {
  const backendServers = Deno.env.get("BACKEND_SERVERS") || "localhost:4001,localhost:4002,localhost:4003";
  const strategy = (Deno.env.get("LB_STRATEGY") || "round-robin") as "round-robin" | "random" | "least-conn";
  const port = parseInt(Deno.env.get("PROXY_PORT") || "8080");
  const adminPort = parseInt(Deno.env.get("ADMIN_PORT") || "9901");
  
  await startEnvoyProxy({
    backendServers,
    strategy,
    port,
    adminPort
  });
}