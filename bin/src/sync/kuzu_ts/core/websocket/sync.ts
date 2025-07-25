/**
 * WebSocket Sync Implementation
 * WebSocket同期実装
 */

import type { WebSocketSync, WebSocketMessage } from "./types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";

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
          console.log("WebSocket connected");
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
            console.error("Failed to parse WebSocket message:", error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
        };
        
        this.ws.onclose = () => {
          console.log("WebSocket disconnected");
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
        console.error("Server error:", message.error);
        break;
        
      case "connected":
        console.log("Server acknowledged connection");
        break;
    }
  }

  private async sendPendingEvents(): Promise<void> {
    if (this.pendingEvents.length > 0) {
      console.log(`Sending ${this.pendingEvents.length} pending events`);
      
      for (const event of this.pendingEvents) {
        await this.sendEvent(event);
      }
      
      this.pendingEvents = [];
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }
    
    this.reconnectAttempts++;
    
    setTimeout(() => {
      console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      if (this.url) {
        this.connect(this.url).catch(console.error);
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }
}