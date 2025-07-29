/**
 * Sync KuzuDB Client
 * WebSocketとインメモリKuzuDBを統合したクライアント
 * DML実行の確認に特化
 */

import { SyncClient } from "./websocket/client.ts";
import { KuzuTsClientImpl } from "./client/kuzu_ts_client.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import * as telemetry from "../telemetry_log.ts";

export interface SyncKuzuClientOptions {
  clientId?: string;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

export class SyncKuzuClient {
  private syncClient: SyncClient;
  private kuzuClient: KuzuTsClientImpl;
  private dmlStats = {
    sent: 0,
    received: 0,
    applied: 0,
    failed: 0
  };
  
  // Template-specific counters
  private templateStats: Map<string, {
    sent: number;
    received: number;
    applied: number;
    failed: number;
  }> = new Map();
  
  // Periodic stats reporter interval
  private statsReporterInterval?: number;
  private statsReportInterval = 5000; // 5 seconds

  constructor(options: SyncKuzuClientOptions = {}) {
    const clientId = options.clientId || `sync-kuzu-${Date.now()}`;
    
    // WebSocketクライアント
    this.syncClient = new SyncClient(clientId, {
      autoReconnect: options.autoReconnect ?? true,
      reconnectDelay: options.reconnectDelay ?? 1000
    });
    
    // KuzuDBクライアント (TypeScript implementation)
    this.kuzuClient = new KuzuTsClientImpl();
    
    // WebSocketイベントをKuzuDBに適用
    this.syncClient.onEvent(async (event) => {
      telemetry.info("Applying remote event to KuzuDB", {
        clientId,
        eventId: event.id,
        template: event.template,
        timestamp: new Date().toISOString()
      });
      
      // Update template-specific stats
      this.incrementTemplateStats(event.template, 'received');
      
      try {
        await this.kuzuClient.applyEvent(event);
        this.dmlStats.applied++;
        this.incrementTemplateStats(event.template, 'applied');
        
        telemetry.info("Remote event applied successfully", {
          clientId,
          eventId: event.id,
          totalApplied: this.dmlStats.applied
        });
      } catch (error) {
        this.dmlStats.failed++;
        this.incrementTemplateStats(event.template, 'failed');
        telemetry.error("Failed to apply remote event", {
          clientId,
          eventId: event.id,
          template: event.template,
          error: error instanceof Error ? error.message : String(error),
          totalFailed: this.dmlStats.failed
        });
      }
      
      this.dmlStats.received++;
    });
  }
  
  async initialize(): Promise<void> {
    telemetry.info("Initializing SyncKuzuClient", {
      clientId: this.syncClient.getClientId()
    });
    
    // KuzuDBを初期化
    await this.kuzuClient.initialize();
    telemetry.info("KuzuDB initialized (in-memory)");
    
    // Start periodic stats reporter
    this.startStatsReporter();
  }
  
  async connect(url: string = "ws://localhost:8080"): Promise<void> {
    await this.syncClient.connect(url);
    telemetry.info("Connected to sync server", {
      url,
      clientId: this.syncClient.getClientId()
    });
  }
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    // ローカルKuzuDBに適用
    const event = await this.kuzuClient.executeTemplate(template, params);
    
    // WebSocket経由で送信
    await this.syncClient.sendEvent(event);
    this.dmlStats.sent++;
    this.incrementTemplateStats(template, 'sent');
    
    telemetry.info("Template executed and sent", {
      clientId: this.syncClient.getClientId(),
      eventId: event.id,
      template: event.template,
      totalSent: this.dmlStats.sent
    });
    
    return event;
  }
  
  getDMLStats() {
    return {
      ...this.dmlStats,
      clientId: this.syncClient.getClientId()
    };
  }
  
  /**
   * Get detailed statistics by template type
   */
  getDetailedStatsByTemplate(): Record<string, {
    sent: number;
    received: number;
    applied: number;
    failed: number;
    successRate: number;
  }> {
    const result: Record<string, any> = {};
    
    this.templateStats.forEach((stats, template) => {
      const total = stats.applied + stats.failed;
      result[template] = {
        ...stats,
        successRate: total > 0 ? (stats.applied / total) * 100 : 0
      };
    });
    
    return result;
  }
  
  /**
   * Helper to increment template-specific stats
   */
  private incrementTemplateStats(template: string, type: 'sent' | 'received' | 'applied' | 'failed'): void {
    if (!this.templateStats.has(template)) {
      this.templateStats.set(template, {
        sent: 0,
        received: 0,
        applied: 0,
        failed: 0
      });
    }
    
    const stats = this.templateStats.get(template)!;
    stats[type]++;
  }
  
  /**
   * Start periodic stats reporter
   */
  private startStatsReporter(): void {
    this.statsReporterInterval = setInterval(() => {
      const overallStats = this.getDMLStats();
      const templateStats = this.getDetailedStatsByTemplate();
      
      telemetry.info("=== DML Statistics Report ===", {
        timestamp: new Date().toISOString(),
        clientId: overallStats.clientId,
        overall: {
          sent: overallStats.sent,
          received: overallStats.received,
          applied: overallStats.applied,
          failed: overallStats.failed,
          successRate: overallStats.applied > 0 || overallStats.failed > 0 
            ? (overallStats.applied / (overallStats.applied + overallStats.failed)) * 100 
            : 0
        },
        byTemplate: templateStats
      });
      
      // Log each template separately for better visibility
      Object.entries(templateStats).forEach(([template, stats]) => {
        telemetry.info(`Template: ${template}`, {
          sent: stats.sent,
          received: stats.received,
          applied: stats.applied,
          failed: stats.failed,
          successRate: `${stats.successRate.toFixed(2)}%`
        });
      });
    }, this.statsReportInterval);
  }
  
  /**
   * Stop periodic stats reporter
   */
  private stopStatsReporter(): void {
    if (this.statsReporterInterval) {
      clearInterval(this.statsReporterInterval);
      this.statsReporterInterval = undefined;
    }
  }
  
  async close(): Promise<void> {
    // Stop stats reporter
    this.stopStatsReporter();
    
    // Log final stats before closing
    telemetry.info("=== Final DML Statistics ===", {
      overall: this.getDMLStats(),
      byTemplate: this.getDetailedStatsByTemplate()
    });
    
    await this.syncClient.close();
    
    // Close native KuzuDB client
    if (this.kuzuClient.close) {
      await this.kuzuClient.close();
    }
  }
}