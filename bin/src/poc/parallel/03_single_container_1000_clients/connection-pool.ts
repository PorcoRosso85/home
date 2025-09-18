/**
 * 高性能コネクションプール - 1000接続対応
 */

import type { Connection } from "./types.ts";

export class ExtremeConnectionPool {
  private connections = new Map<string, Connection>();
  private ipConnectionCount = new Map<string, number>();
  private readonly maxConnections: number;
  private readonly maxConnectionsPerIP: number;
  private connectionIdCounter = 0;
  
  constructor(
    maxConnections: number = 1200, // 1000より少し多めに
    maxConnectionsPerIP: number = 50, // DDoS対策
  ) {
    this.maxConnections = maxConnections;
    this.maxConnectionsPerIP = maxConnectionsPerIP;
  }
  
  canAccept(remoteAddr: Deno.Addr): boolean {
    if (this.connections.size >= this.maxConnections) {
      return false;
    }
    
    // IP制限チェック
    if ("hostname" in remoteAddr) {
      const count = this.ipConnectionCount.get(remoteAddr.hostname) || 0;
      if (count >= this.maxConnectionsPerIP) {
        return false;
      }
    }
    
    return true;
  }
  
  add(conn: Deno.Conn, buffer: Uint8Array): string {
    const id = `conn-${Date.now()}-${this.connectionIdCounter++}`;
    
    const connection: Connection = {
      id,
      conn,
      buffer,
      state: "active",
      lastActivity: Date.now(),
    };
    
    this.connections.set(id, connection);
    
    // IP別カウント更新
    const remoteAddr = conn.remoteAddr;
    if ("hostname" in remoteAddr) {
      const current = this.ipConnectionCount.get(remoteAddr.hostname) || 0;
      this.ipConnectionCount.set(remoteAddr.hostname, current + 1);
    }
    
    return id;
  }
  
  remove(id: string): void {
    const connection = this.connections.get(id);
    if (!connection) return;
    
    this.connections.delete(id);
    
    // IP別カウント更新
    const remoteAddr = connection.conn.remoteAddr;
    if ("hostname" in remoteAddr) {
      const current = this.ipConnectionCount.get(remoteAddr.hostname) || 0;
      if (current > 1) {
        this.ipConnectionCount.set(remoteAddr.hostname, current - 1);
      } else {
        this.ipConnectionCount.delete(remoteAddr.hostname);
      }
    }
    
    // 接続をクローズ
    try {
      connection.conn.close();
    } catch {
      // 既にクローズされている可能性
    }
  }
  
  get(id: string): Connection | undefined {
    return this.connections.get(id);
  }
  
  // タイムアウトした接続をクリーンアップ
  cleanupStale(maxAge: number = 60000): number {
    const now = Date.now();
    const staleIds: string[] = [];
    
    for (const [id, conn] of this.connections) {
      if (now - conn.lastActivity > maxAge) {
        staleIds.push(id);
      }
    }
    
    for (const id of staleIds) {
      this.remove(id);
    }
    
    return staleIds.length;
  }
  
  getStats(): {
    total: number;
    byState: Record<string, number>;
    byIP: Array<{ ip: string; count: number }>;
  } {
    const byState: Record<string, number> = {};
    
    for (const conn of this.connections.values()) {
      byState[conn.state] = (byState[conn.state] || 0) + 1;
    }
    
    const byIP = Array.from(this.ipConnectionCount.entries())
      .map(([ip, count]) => ({ ip, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // トップ10のみ
    
    return {
      total: this.connections.size,
      byState,
      byIP,
    };
  }
}