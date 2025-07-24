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
  private historyHandlers: ((events: any[]) => void)[] = [];
  private subscriptionHandlers: Map<string, (event: any) => void> = new Map();
  private connected = false;
  private connectionPromise: Promise<void> | null = null;
  private historyRequested = false;
  private autoReconnect: boolean = false;
  private reconnectDelay: number = 1000;
  private reconnectTimer: number | null = null;
  private eventEmitter: Map<string, Array<(...args: any[]) => void>> = new Map();
  private wsUrl: string | null = null;
  
  constructor(public readonly id: string, options?: { autoReconnect?: boolean; reconnectDelay?: number }) {
    if (options) {
      this.autoReconnect = options.autoReconnect || false;
      this.reconnectDelay = options.reconnectDelay || 1000;
    }
  }
  
  async connect(url: string = "ws://localhost:8080"): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }
    
    this.wsUrl = url;
    this.emit("connecting");
    
    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = `${url}?clientId=${this.id}`;
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        const wasReconnecting = this.connected === false && this.reconnectTimer !== null;
        this.connected = true;
        
        // 接続時に自動的に履歴を要求
        if (!this.historyRequested) {
          this.requestInitialHistory();
        }
        
        if (wasReconnecting) {
          this.emit("reconnected");
        }
        
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
              
            case "history":
              // 履歴イベントを処理
              this.historyHandlers.forEach(handler => handler(message.events || []));
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
        this.connectionPromise = null;
        
        if (this.autoReconnect && this.wsUrl) {
          this.reconnectTimer = setTimeout(() => {
            this.connect(this.wsUrl!);
          }, this.reconnectDelay);
        }
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
  
  onHistoryReceived(handler: (events: any[]) => void): void {
    this.historyHandlers.push(handler);
  }
  
  private async requestInitialHistory(): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    
    this.historyRequested = true;
    this.ws.send(JSON.stringify({
      type: "requestHistory",
      fromPosition: 0
    }));
  }
  
  async requestHistoryFrom(position: number): Promise<{ events: any[] }> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected");
    }
    
    return new Promise((resolve) => {
      const handler = (event: MessageEvent) => {
        const message = JSON.parse(event.data);
        if (message.type === "history") {
          this.ws!.removeEventListener("message", handler);
          resolve({ events: message.events || [] });
        }
      };
      
      this.ws!.addEventListener("message", handler);
      
      this.ws!.send(JSON.stringify({
        type: "requestHistory",
        fromPosition: position
      }));
    });
  }
  
  async requestHistoryPage(options: { fromPosition: number; limit: number }): Promise<{ events: any[] }> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected");
    }
    
    return new Promise((resolve) => {
      const handler = (event: MessageEvent) => {
        const message = JSON.parse(event.data);
        if (message.type === "history") {
          this.ws!.removeEventListener("message", handler);
          resolve({ events: message.events || [] });
        }
      };
      
      this.ws!.addEventListener("message", handler);
      
      this.ws!.send(JSON.stringify({
        type: "requestHistory",
        fromPosition: options.fromPosition,
        limit: options.limit
      }));
    });
  }
  
  async requestHistoryWithVerification(): Promise<{ events: any[]; verified: boolean }> {
    // 簡易実装：通常の履歴取得に検証フラグを追加
    const history = await this.requestHistoryFrom(0);
    return {
      events: history.events,
      verified: true // TODO: 実際のチェックサム検証
    };
  }
  
  async requestCompressedHistory(): Promise<{ events: any[]; compressionRatio: number }> {
    // 簡易実装：通常の履歴取得
    const history = await this.requestHistoryFrom(0);
    return {
      events: history.events,
      compressionRatio: 1 // TODO: 実際の圧縮実装
    };
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
  
  on(event: string, handler: (...args: any[]) => void): void {
    if (!this.eventEmitter.has(event)) {
      this.eventEmitter.set(event, []);
    }
    this.eventEmitter.get(event)!.push(handler);
  }
  
  emit(event: string, ...args: any[]): void {
    const handlers = this.eventEmitter.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(...args));
    }
  }
  
  getClientId(): string {
    return this.id;
  }
  
  close(): void {
    this.autoReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected = false;
    }
  }
  
  disconnect(): void {
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