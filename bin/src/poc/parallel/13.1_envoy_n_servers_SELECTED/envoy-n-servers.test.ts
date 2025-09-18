import { assertEquals, assertExists, assertThrows } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { 
  parseServers, 
  createLoadBalancer, 
  checkAllServers,
  LoadBalancer,
  ServerInfo,
  HealthStatus
} from "./envoy-n-servers.ts";

describe("parseServers", () => {
  it("test_parseServers_with_valid_string_returns_server_list", () => {
    const input = "localhost:4001,localhost:4002,localhost:4003";
    const servers = parseServers(input);
    
    assertEquals(servers.length, 3);
    assertEquals(servers[0].id, "server-1");
    assertEquals(servers[0].host, "localhost");
    assertEquals(servers[0].port, 4001);
    assertEquals(servers[1].id, "server-2");
    assertEquals(servers[2].id, "server-3");
  });
  
  it("test_parseServers_with_empty_string_throws_error", () => {
    assertThrows(
      () => parseServers(""),
      Error,
      "BACKEND_SERVERS cannot be empty"
    );
  });
  
  it("test_parseServers_with_single_server_returns_one_item", () => {
    const servers = parseServers("api.example.com:8080");
    assertEquals(servers.length, 1);
    assertEquals(servers[0].host, "api.example.com");
    assertEquals(servers[0].port, 8080);
  });
});

describe("LoadBalancer", () => {
  let servers: ServerInfo[];
  
  beforeEach(() => {
    servers = [
      { id: "server-1", host: "localhost", port: 4001, url: "http://localhost:4001", healthy: true, connections: 0 },
      { id: "server-2", host: "localhost", port: 4002, url: "http://localhost:4002", healthy: true, connections: 0 },
      { id: "server-3", host: "localhost", port: 4003, url: "http://localhost:4003", healthy: true, connections: 0 }
    ];
  });
  
  describe("Round Robin Strategy", () => {
    it("test_roundRobin_distributes_requests_evenly", () => {
      const lb = createLoadBalancer(servers, "round-robin");
      
      // 最初の一巡
      assertEquals(lb.selectServer().id, "server-1");
      assertEquals(lb.selectServer().id, "server-2");
      assertEquals(lb.selectServer().id, "server-3");
      
      // 二巡目も同じ順序
      assertEquals(lb.selectServer().id, "server-1");
      assertEquals(lb.selectServer().id, "server-2");
      assertEquals(lb.selectServer().id, "server-3");
    });
    
    it("test_roundRobin_skips_unhealthy_servers", () => {
      servers[1].healthy = false; // server-2を不健全に
      const lb = createLoadBalancer(servers, "round-robin");
      
      // server-2をスキップ
      assertEquals(lb.selectServer().id, "server-1");
      assertEquals(lb.selectServer().id, "server-3");
      assertEquals(lb.selectServer().id, "server-1");
    });
  });
  
  describe("Random Strategy", () => {
    it("test_random_returns_valid_server", () => {
      const lb = createLoadBalancer(servers, "random");
      
      for (let i = 0; i < 100; i++) {
        const server = lb.selectServer();
        assertExists(servers.find(s => s.id === server.id));
      }
    });
    
    it("test_random_distributes_approximately_even", () => {
      const lb = createLoadBalancer(servers, "random");
      const distribution: Record<string, number> = {
        "server-1": 0,
        "server-2": 0,
        "server-3": 0
      };
      
      // 1000回のリクエストで分散を確認
      for (let i = 0; i < 1000; i++) {
        const server = lb.selectServer();
        distribution[server.id]++;
      }
      
      // 各サーバーが200-466の範囲（期待値333の±40%）
      Object.values(distribution).forEach(count => {
        assertEquals(count > 200 && count < 466, true);
      });
    });
  });
  
  describe("Least Connections Strategy", () => {
    it("test_leastConnections_selects_server_with_fewest_connections", () => {
      servers[0].connections = 5;
      servers[1].connections = 2;
      servers[2].connections = 8;
      
      const lb = createLoadBalancer(servers, "least-conn");
      
      // 最小接続数のserver-2が選ばれる
      assertEquals(lb.selectServer().id, "server-2");
      
      // 接続数を更新
      servers[1].connections = 10;
      
      // 次は最小のserver-1が選ばれる
      assertEquals(lb.selectServer().id, "server-1");
    });
    
    it("test_leastConnections_handles_tie_with_round_robin", () => {
      // すべて同じ接続数
      servers.forEach(s => s.connections = 5);
      
      const lb = createLoadBalancer(servers, "least-conn");
      
      // タイの場合はラウンドロビン順
      assertEquals(lb.selectServer().id, "server-1");
      assertEquals(lb.selectServer().id, "server-2");
      assertEquals(lb.selectServer().id, "server-3");
    });
  });
  
  describe("No healthy servers", () => {
    it("test_allUnhealthy_throws_error", () => {
      servers.forEach(s => s.healthy = false);
      const lb = createLoadBalancer(servers, "round-robin");
      
      assertThrows(
        () => lb.selectServer(),
        Error,
        "No healthy servers available"
      );
    });
  });
});

describe("Health Check", () => {
  it("test_checkAllServers_returns_health_status_for_all", async () => {
    const servers: ServerInfo[] = [
      { id: "server-1", host: "localhost", port: 4001, url: "http://localhost:4001", healthy: true, connections: 0 },
      { id: "server-2", host: "localhost", port: 4002, url: "http://localhost:4002", healthy: true, connections: 0 },
      { id: "server-3", host: "localhost", port: 4003, url: "http://localhost:4003", healthy: true, connections: 0 }
    ];
    
    const results = await checkAllServers(servers);
    
    assertEquals(results.length, 3);
    results.forEach((result: HealthStatus) => {
      assertExists(result.serverId);
      assertExists(result.healthy !== undefined);
      assertExists(result.responseTime);
    });
  });
  
  it("test_checkAllServers_handles_failed_servers", async () => {
    const servers: ServerInfo[] = [
      { id: "server-1", host: "localhost", port: 4001, url: "http://localhost:4001", healthy: true, connections: 0 },
      { id: "server-2", host: "unreachable", port: 9999, url: "http://unreachable:9999", healthy: true, connections: 0 }
    ];
    
    const results = await checkAllServers(servers);
    
    // 失敗したサーバーも結果に含まれる
    assertEquals(results.length, 2);
    const failedServer = results.find((r: HealthStatus) => r.serverId === "server-2");
    assertEquals(failedServer?.healthy, false);
    assertExists(failedServer?.error);
  });
});

describe("Dynamic server management", () => {
  it("test_addServer_increases_server_count", () => {
    const servers = parseServers("localhost:4001,localhost:4002");
    const lb = createLoadBalancer(servers, "round-robin");
    
    assertEquals(lb.getServerCount(), 2);
    
    // 新しいサーバーを追加
    const newServer: ServerInfo = {
      id: "server-3",
      host: "localhost",
      port: 4003,
      url: "http://localhost:4003",
      healthy: true,
      connections: 0
    };
    
    lb.addServer(newServer);
    assertEquals(lb.getServerCount(), 3);
    
    // ラウンドロビンに含まれることを確認
    const selectedIds = new Set<string>();
    for (let i = 0; i < 3; i++) {
      selectedIds.add(lb.selectServer().id);
    }
    assertEquals(selectedIds.has("server-3"), true);
  });
  
  it("test_removeServer_decreases_server_count", () => {
    const servers = parseServers("localhost:4001,localhost:4002,localhost:4003");
    const lb = createLoadBalancer(servers, "round-robin");
    
    assertEquals(lb.getServerCount(), 3);
    
    lb.removeServer("server-2");
    assertEquals(lb.getServerCount(), 2);
    
    // server-2が選ばれないことを確認
    for (let i = 0; i < 10; i++) {
      const selected = lb.selectServer();
      assertEquals(selected.id !== "server-2", true);
    }
  });
});