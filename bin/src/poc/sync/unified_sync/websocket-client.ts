/**
 * WebSocket Client for Multi-Browser Sync Tests
 * テスト用のWebSocketクライアント実装
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - モックフリー実装
 * - TDD Green Phase
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";

// ========== クライアント実装 ==========

export class SyncClient {
  ws: WebSocket | null = null;
  private eventHandlers: ((event: any) => void)[] = [];
  private errorHandlers: ((error: any) => void)[] = [];
  private subscriptionHandlers: Map<string, (event: any) => void> = new Map();
  private connected = false;
  private connectionPromise: Promise<void> | null = null;
  
  constructor(public readonly id: string) {}
  
  async connect(url: string = "ws://localhost:8080"): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }
    
    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = `${url}?clientId=${this.id}`;
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        this.connected = true;
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case "event":
              // 全体イベントハンドラー
              this.eventHandlers.forEach(handler => handler(message.payload));
              
              // テンプレート別ハンドラー
              const templateHandler = this.subscriptionHandlers.get(message.payload.template);
              if (templateHandler) {
                templateHandler(message.payload);
              }
              break;
              
            case "error":
              this.errorHandlers.forEach(handler => handler(message));
              break;
          }
        } catch (error) {
          console.error("Error parsing message:", error);
        }
      };
      
      this.ws.onerror = (event) => {
        const error = new Error("WebSocket error");
        this.errorHandlers.forEach(handler => handler(error));
        reject(error);
      };
      
      this.ws.onclose = () => {
        this.connected = false;
      };
    });
    
    return this.connectionPromise;
  }
  
  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }
  
  async sendEvent(event: any): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected");
    }
    
    this.ws.send(JSON.stringify({
      type: "event",
      payload: event
    }));
  }
  
  async requestHistory(params: { fromPosition: number }): Promise<{ events: any[] }> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected");
    }
    
    return new Promise((resolve) => {
      const handler = (event: MessageEvent) => {
        const message = JSON.parse(event.data);
        if (message.type === "history") {
          this.ws!.removeEventListener("message", handler);
          resolve({ events: message.events });
        }
      };
      
      this.ws!.addEventListener("message", handler);
      
      this.ws!.send(JSON.stringify({
        type: "requestHistory",
        fromPosition: params.fromPosition
      }));
    });
  }
  
  onEvent(handler: (event: any) => void): void {
    this.eventHandlers.push(handler);
  }
  
  onError(handler: (error: any) => void): void {
    this.errorHandlers.push(handler);
  }
  
  subscribe(template: string, handler: (event: any) => void): void {
    this.subscriptionHandlers.set(template, handler);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "subscribe",
        template: template
      }));
    }
  }
  
  async disconnect(): Promise<void> {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected = false;
    }
  }
}

// ========== ヘルパー関数 ==========

export async function connectToServer(clientId: string): Promise<SyncClient> {
  const client = new SyncClient(clientId);
  await client.connect();
  return client;
}

export async function getServerState(): Promise<any> {
  // HTTPエンドポイントを使用（WebSocket接続を避ける）
  const response = await fetch("http://localhost:8080/state");
  return await response.json();
}

export async function waitFor(condition: () => boolean, timeout = 1000): Promise<void> {
  const start = Date.now();
  while (!condition()) {
    if (Date.now() - start > timeout) {
      throw new Error("Timeout waiting for condition");
    }
    await new Promise(resolve => setTimeout(resolve, 10));
  }
}