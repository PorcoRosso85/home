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

  trackEvent(event: TemplateEvent): void {
    this.totalEvents++;
    
    // Track event types
    this.eventTypes[event.template] = (this.eventTypes[event.template] || 0) + 1;
    
    // Track latency (simplified - in real implementation would measure actual latency)
    const latency = Math.random() * 50; // Simulated latency 0-50ms
    this.latencies.push(latency);
  }

  getStats(): MetricsStats {
    const averageLatency = this.latencies.length > 0
      ? this.latencies.reduce((a, b) => a + b, 0) / this.latencies.length
      : 0;
    
    return {
      totalEvents: this.totalEvents,
      eventTypes: { ...this.eventTypes },
      averageLatency,
      errors: this.errors
    };
  }
}