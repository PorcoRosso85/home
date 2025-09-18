// 外部依存（インフラストラクチャ層）との接続部
// bin/docs規約準拠: エラーを戻り値として扱う

import { Pool, PoolClient } from "https://deno.land/x/postgres@v0.17.0/mod.ts";
import type { DatabaseConfig, ServerResult, UserProfile, GlobalSetting, ServerError } from "../types/server.ts";

export class DatabaseAdapter {
  private pool: Pool;
  
  constructor(config: DatabaseConfig) {
    this.pool = new Pool({
      hostname: config.hostname,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      max: 20
    }, 3);
  }
  
  async getUserProfile(userId: string): Promise<ServerResult<UserProfile>> {
    let client: PoolClient | null = null;
    
    try {
      client = await this.pool.connect();
      const result = await client.queryObject<UserProfile>(
        'SELECT user_id as "userId", created_at as "createdAt" FROM users WHERE user_id = $1',
        [userId]
      );
    
      if (result.rows.length === 0) {
        // 新規ユーザーの作成
        const insertResult = await client.queryObject<UserProfile>(
          'INSERT INTO users (user_id, created_at) VALUES ($1, NOW()) RETURNING user_id as "userId", created_at as "createdAt"',
          [userId]
        );
        return { ok: true, data: insertResult.rows[0] };
      }
      
      return { ok: true, data: result.rows[0] };
    } catch (error) {
      const serverError: ServerError = {
        code: 'DB_ERROR',
        message: error instanceof Error ? error.message : 'Database error',
        details: error
      };
      return { ok: false, error: serverError };
    } finally {
      if (client) client.release();
    }
  }
  
  async upsertGlobalSetting(key: string, value: unknown, synced = false): Promise<ServerResult<GlobalSetting>> {
    let client: PoolClient | null = null;
    
    try {
      client = await this.pool.connect();
      const result = await client.queryObject<GlobalSetting>(
        `INSERT INTO global_settings (key, value, updated_at, synced) 
         VALUES ($1, $2, NOW(), $3) 
         ON CONFLICT (key) DO UPDATE 
         SET value = $2, updated_at = NOW(), synced = $3
         RETURNING key, value, updated_at as "updatedAt", synced`,
        [key, JSON.stringify(value), synced]
      );
      
      return { ok: true, data: result.rows[0] };
    } catch (error) {
      const serverError: ServerError = {
        code: 'DB_ERROR',
        message: error instanceof Error ? error.message : 'Database error',
        details: error
      };
      return { ok: false, error: serverError };
    } finally {
      if (client) client.release();
    }
  }
  
  async checkConnection(): Promise<ServerResult<boolean>> {
    try {
      const client = await this.pool.connect();
      await client.queryArray('SELECT 1');
      client.release();
      return { ok: true, data: true };
    } catch (error) {
      const serverError: ServerError = {
        code: 'DB_CONNECTION_ERROR',
        message: error instanceof Error ? error.message : 'Connection failed',
        details: error
      };
      return { ok: false, error: serverError };
    }
  }
  
  async getMetrics(): Promise<ServerResult<{ totalUsers: number; totalSettings: number; pendingSyncs: number }>> {
    let client: PoolClient | null = null;
    
    try {
      client = await this.pool.connect();
      const result = await client.queryObject<{ total_users: number; total_settings: number; pending_syncs: number }>(`
        SELECT 
          (SELECT COUNT(*) FROM users) as total_users,
          (SELECT COUNT(*) FROM global_settings) as total_settings,
          (SELECT COUNT(*) FROM sync_queue WHERE processed = false) as pending_syncs
      `);
      
      const row = result.rows[0];
      return { 
        ok: true, 
        data: {
          totalUsers: Number(row.total_users),
          totalSettings: Number(row.total_settings),
          pendingSyncs: Number(row.pending_syncs)
        }
      };
    } catch (error) {
      const serverError: ServerError = {
        code: 'DB_ERROR',
        message: error instanceof Error ? error.message : 'Metrics query failed',
        details: error
      };
      return { ok: false, error: serverError };
    } finally {
      if (client) client.release();
    }
  }
  
  async close(): Promise<void> {
    await this.pool.end();
  }
  
  getPoolStats() {
    return {
      size: this.pool.size,
      available: this.pool.available
    };
  }
}