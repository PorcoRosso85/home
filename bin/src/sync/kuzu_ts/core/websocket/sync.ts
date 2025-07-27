/**
 * WebSocket Sync Implementation
 * WebSocket同期実装
 */

import type { WebSocketSync, WebSocketMessage } from "./types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";
import * as telemetry from "../../telemetry_log.ts";

export class WebSocketSyncImpl implements WebSocketSync {
  private ws?: WebSocket;
  private url?: string;
  private eventHandlers: Array<(event: TemplateEvent) => void> = [];
  private pendingEvents: TemplateEvent[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  async connect(url: string): Promise<void> {
    this.url = url;
    
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          telemetry.info("WebSocket connected", { url: this.url });
          this.reconnectAttempts = 0;
          
          // Send pending events
          this.sendPendingEvents();
          
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            telemetry.error("Failed to parse WebSocket message", { error: error.message });
          }
        };
        
        this.ws.onerror = (error) => {
          telemetry.error("WebSocket error", { error: error.toString() });
        };
        
        this.ws.onclose = () => {
          telemetry.info("WebSocket disconnected", { url: this.url });
          this.attemptReconnect();
        };
        
      } catch (error) {
        reject(error);
      }
    });
  }

  async sendEvent(event: TemplateEvent): Promise<void> {
    if (!this.isConnected()) {
      // Queue event for later
      this.pendingEvents.push(event);
      return;
    }
    
    const message: WebSocketMessage = {
      type: "event",
      payload: event
    };
    
    this.ws!.send(JSON.stringify(message));
  }

  onEvent(handler: (event: TemplateEvent) => void): void {
    this.eventHandlers.push(handler);
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  async getPendingEvents(): Promise<TemplateEvent[]> {
    return [...this.pendingEvents];
  }

  // Private methods

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case "event":
        const event = message.payload as TemplateEvent;
        this.eventHandlers.forEach(handler => handler(event));
        break;
        
      case "sync":
        // Handle sync response
        break;
        
      case "error":
        telemetry.error("Server error", { error: message.error });
        break;
        
      case "connected":
        telemetry.info("Server acknowledged connection", { clientId: (message.payload as any)?.clientId });
        break;
    }
  }

  private async sendPendingEvents(): Promise<void> {
    if (this.pendingEvents.length > 0) {
      telemetry.info("Sending pending events", { count: this.pendingEvents.length });
      
      for (const event of this.pendingEvents) {
        await this.sendEvent(event);
      }
      
      this.pendingEvents = [];
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      telemetry.error("Max reconnection attempts reached", { maxAttempts: this.maxReconnectAttempts });
      return;
    }
    
    this.reconnectAttempts++;
    
    setTimeout(() => {
      telemetry.info("Attempting reconnect", { 
        attempt: this.reconnectAttempts, 
        maxAttempts: this.maxReconnectAttempts 
      });
      if (this.url) {
        this.connect(this.url).catch(error => telemetry.error("Reconnect failed", { error: error.message }));
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }
}