// サーバー実装
// bin/docs規約準拠: エラーを戻り値として扱う、高階関数で柔軟性を実現

import type { 
  ServerConfig, 
  ServerResult, 
  ServerError, 
  UserProfile, 
  HealthStatus,
  MetricsData 
} from "./types/server.ts";
import { isInPartition, getCorrectServer } from "./core/partition.ts";
import { DatabaseAdapter } from "./adapters/database.ts";
import { HttpClient } from "./adapters/http-client.ts";

export class DualServerApplication {
  private config: ServerConfig;
  private db: DatabaseAdapter;
  private peerClient: HttpClient;
  private server: Deno.HttpServer | null = null;
  private peerHealthy = true;
  
  constructor(config: ServerConfig) {
    this.config = config;
    this.db = new DatabaseAdapter(config.database);
    this.peerClient = new HttpClient(config.peerServer);
    
    this.startHealthCheck();
  }
  
  /**
   * リクエストハンドラー（高階関数パターン）
   */
  private createRequestHandler() {
    return async (request: Request): Promise<Response> => {
      const result = await this.handleRequest(request);
      
      if (!result.ok) {
        return new Response(JSON.stringify({
          error: result.error.message,
          code: result.error.code,
          server: this.config.name
        }), {
          status: result.error.code === 'MISDIRECTED_REQUEST' ? 421 : 500,
          headers: { 'content-type': 'application/json' }
        });
      }
      
      return result.data;
    };
  }
  
  private async handleRequest(request: Request): Promise<ServerResult<Response>> {
    const url = new URL(request.url);
    const userId = request.headers.get('x-user-id') || url.searchParams.get('userId');
    
    // ルーティングチェック
    if (userId && !isInPartition(userId, this.config.partitionKey)) {
      const error: ServerError = {
        code: 'MISDIRECTED_REQUEST',
        message: 'Misdirected Request',
        server: getCorrectServer(userId, this.config.name, this.config.partitionKey, this.config.peerServer)
      };
      return { ok: false, error };
    }
    
    // ルーティング
    switch (url.pathname) {
      case '/health':
        return this.handleHealth();
      
      case '/api/profile':
        if (request.method === 'GET' && userId) {
          return this.handleGetProfile(userId);
        }
        break;
      
      case '/api/global-settings':
        if (request.method === 'PUT') {
          return this.handleUpdateGlobalSettings(request);
        }
        break;
      
      case '/api/sync/global-settings':
        if (request.method === 'POST') {
          return this.handleSyncGlobalSettings(request);
        }
        break;
      
      case '/api/metrics':
        if (request.method === 'GET') {
          return this.handleGetMetrics();
        }
        break;
    }
    
    // クロスサーバークエリのパス処理
    const userMatch = url.pathname.match(/^\/api\/user\/([^\/]+)\/profile$/);
    if (userMatch && request.method === 'GET') {
      return this.handleCrossServerQuery(userMatch[1], userId || '');
    }
    
    return { 
      ok: true, 
      data: new Response('Not Found', { status: 404 }) 
    };
  }
  
  private async handleHealth(): Promise<ServerResult<Response>> {
    const dbResult = await this.db.checkConnection();
    const dbStatus = dbResult.ok ? 'connected' : 'disconnected';
    
    // ピアヘルスチェック
    let peerStatus: 'healthy' | 'unreachable' | 'unknown' = 'unknown';
    const peerHealthResult = await this.peerClient.get<HealthStatus>('/health');
    if (peerHealthResult.ok && peerHealthResult.data.status === 200) {
      peerStatus = 'healthy';
    } else {
      peerStatus = 'unreachable';
    }
    
    const health: HealthStatus = {
      status: dbResult.ok ? 'healthy' : 'unhealthy',
      server: this.config.name,
      database: dbStatus,
      peer: peerStatus,
      uptime: performance.now() / 1000
    };
    
    return {
      ok: true,
      data: new Response(JSON.stringify(health), {
        status: dbResult.ok ? 200 : 503,
        headers: { 'content-type': 'application/json' }
      })
    };
  }
  
  private async handleGetProfile(userId: string): Promise<ServerResult<Response>> {
    const profileResult = await this.db.getUserProfile(userId);
    
    if (!profileResult.ok) {
      return { ok: false, error: profileResult.error };
    }
    
    const profile: UserProfile = {
      ...profileResult.data,
      server: this.config.name,
      partition: this.config.partitionKey
    };
    
    return {
      ok: true,
      data: new Response(JSON.stringify(profile), {
        headers: { 'content-type': 'application/json' }
      })
    };
  }
  
  private async handleUpdateGlobalSettings(request: Request): Promise<ServerResult<Response>> {
    try {
      const body = await request.json();
      const { setting, value } = body;
      
      const result = await this.db.upsertGlobalSetting(setting, value);
      
      if (!result.ok) {
        return { ok: false, error: result.error };
      }
      
      // ピアに同期（非同期、エラーは無視）
      this.syncToPeer('/api/sync/global-settings', { setting, value });
      
      return {
        ok: true,
        data: new Response(JSON.stringify({ 
          success: true, 
          server: this.config.name 
        }), {
          headers: { 'content-type': 'application/json' }
        })
      };
    } catch (error) {
      const serverError: ServerError = {
        code: 'REQUEST_PARSE_ERROR',
        message: 'Invalid request body',
        details: error
      };
      return { ok: false, error: serverError };
    }
  }
  
  private async handleSyncGlobalSettings(request: Request): Promise<ServerResult<Response>> {
    try {
      const body = await request.json();
      const { setting, value } = body;
      
      const result = await this.db.upsertGlobalSetting(setting, value, true);
      
      if (!result.ok) {
        return { ok: false, error: result.error };
      }
      
      return {
        ok: true,
        data: new Response(JSON.stringify({ success: true }), {
          headers: { 'content-type': 'application/json' }
        })
      };
    } catch (error) {
      const serverError: ServerError = {
        code: 'SYNC_ERROR',
        message: 'Sync failed',
        details: error
      };
      return { ok: false, error: serverError };
    }
  }
  
  private async handleCrossServerQuery(targetUserId: string, requestingUserId: string): Promise<ServerResult<Response>> {
    if (!isInPartition(targetUserId, this.config.partitionKey)) {
      // 他のサーバーから取得
      console.log(`Cross-server query to ${this.config.peerServer} for user ${targetUserId}`);
      
      const result = await this.peerClient.get<UserProfile>(
        '/api/profile',
        { userId: targetUserId },
        { 'X-User-Id': targetUserId, 'X-Requesting-Server': this.config.name }
      );
      
      if (!result.ok) {
        return { ok: false, error: result.error };
      }
      
      if (result.data.status !== 200 || !result.data.data) {
        const error: ServerError = {
          code: 'CROSS_SERVER_ERROR',
          message: 'Cross-server query failed',
          details: `Status: ${result.data.status}`
        };
        return { ok: false, error };
      }
      
      const response = {
        ...result.data.data,
        fetched_from: result.data.data.server,
        requested_by: requestingUserId
      };
      
      return {
        ok: true,
        data: new Response(JSON.stringify(response), {
          headers: { 'content-type': 'application/json' }
        })
      };
    } else {
      // ローカルで処理
      return this.handleGetProfile(targetUserId);
    }
  }
  
  private async handleGetMetrics(): Promise<ServerResult<Response>> {
    const metricsResult = await this.db.getMetrics();
    
    if (!metricsResult.ok) {
      return { ok: false, error: metricsResult.error };
    }
    
    const poolStats = this.db.getPoolStats();
    
    const metrics: MetricsData = {
      server: this.config.name,
      partition: this.config.partitionKey,
      ...metricsResult.data,
      connections: {
        active: poolStats.size,
        idle: poolStats.available,
        waiting: 0
      }
    };
    
    return {
      ok: true,
      data: new Response(JSON.stringify(metrics), {
        headers: { 'content-type': 'application/json' }
      })
    };
  }
  
  private async syncToPeer(path: string, data: unknown): Promise<void> {
    if (!this.peerHealthy) {
      console.warn('Peer is unhealthy, skipping sync');
      return;
    }
    
    const result = await this.peerClient.post(path, data, {
      'X-Sync-From': this.config.name
    });
    
    if (!result.ok) {
      console.error('Sync to peer failed:', result.error);
    }
  }
  
  private startHealthCheck(): void {
    setInterval(async () => {
      const result = await this.peerClient.get<HealthStatus>('/health');
      this.peerHealthy = result.ok && result.data.status === 200;
      
      if (!this.peerHealthy) {
        console.warn(`Peer ${this.config.peerServer} is unhealthy`);
      }
    }, 10000); // 10秒ごと
  }
  
  async start(): Promise<void> {
    const port = this.config.port;
    
    console.log(`Server ${this.config.name} (${this.config.partitionKey}) listening on port ${port}`);
    console.log(`Peer server: ${this.config.peerServer}`);
    
    this.server = Deno.serve(
      { port },
      this.createRequestHandler()
    );
    
    // グレースフルシャットダウン
    Deno.addSignalListener("SIGTERM", () => {
      console.log('SIGTERM received, shutting down...');
      this.shutdown();
    });
    
    await this.server.finished;
  }
  
  async shutdown(): Promise<void> {
    await this.db.close();
    if (this.server) {
      await this.server.shutdown();
    }
  }
}