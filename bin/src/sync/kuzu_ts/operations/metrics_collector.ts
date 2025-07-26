/**
 * Metrics Collector Implementation
 * メトリクス収集実装
 */

import type { MetricsCollector, MetricsStats, BrowserKuzuClient } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

export class MetricsCollectorImpl implements MetricsCollector {
  private totalEvents = 0;
  private eventTypes: Record<string, number> = {};
  private latencies: number[] = [];
  private errors = 0;
  private client?: BrowserKuzuClient;
  private compressionRatios: number[] = [];
  private eventTimestamps: number[] = [];
  private readonly maxMetricAge = 5 * 60 * 1000; // 5 minutes

  startTracking(client: BrowserKuzuClient): void {
    this.client = client;
    
    // Intercept only top-level calls
    const originalExecute = client.executeTemplate.bind(client);
    let isTracking = false;
    
    client.executeTemplate = async (template: string, params: Record<string, any>) => {
      const shouldTrack = !isTracking;
      if (shouldTrack) {
        isTracking = true;
      }
      
      const event = await originalExecute(template, params);
      
      if (shouldTrack) {
        this.trackEvent(event);
        isTracking = false;
      }
      
      return event;
    };
  }

  trackEvent(event: TemplateEvent, latency?: number): void {
    const now = Date.now();
    this.totalEvents++;
    
    // Track event types
    this.eventTypes[event.template] = (this.eventTypes[event.template] || 0) + 1;
    
    // Track latency
    if (latency !== undefined) {
      this.latencies.push(latency);
    }
    
    // Track timestamp for rate calculation
    this.eventTimestamps.push(now);
    
    // Clean up old metrics
    this.cleanupOldMetrics(now);
  }
  
  trackCompressionRatio(ratio: number): void {
    this.compressionRatios.push(ratio);
    // Keep only last 100 compression ratios
    if (this.compressionRatios.length > 100) {
      this.compressionRatios.shift();
    }
  }
  
  private cleanupOldMetrics(now: number): void {
    const cutoff = now - this.maxMetricAge;
    this.eventTimestamps = this.eventTimestamps.filter(ts => ts > cutoff);
    
    // Keep only recent latencies (last 1000)
    if (this.latencies.length > 1000) {
      this.latencies = this.latencies.slice(-1000);
    }
  }

  getStats(): MetricsStats {
    const averageLatency = this.latencies.length > 0
      ? this.latencies.reduce((a, b) => a + b, 0) / this.latencies.length
      : 0;
    
    const averageCompressionRatio = this.compressionRatios.length > 0
      ? this.compressionRatios.reduce((a, b) => a + b, 0) / this.compressionRatios.length
      : 0;
    
    // Calculate events per minute based on recent timestamps
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const recentEvents = this.eventTimestamps.filter(ts => ts > oneMinuteAgo).length;
    
    return {
      totalEvents: this.totalEvents,
      eventTypes: { ...this.eventTypes },
      averageLatency,
      errors: this.errors,
      compressionRatio: averageCompressionRatio,
      eventsPerMinute: recentEvents
    };
  }
}