/**
 * Bun WebSocket Client
 * Deno版と同等の機能をBunで実装
 */

// Using require() to load the packaged kuzu module from persistence/kuzu_ts
// This follows the pattern from persistence/kuzu_ts/examples/test_bun_package/test.ts
const kuzu = require("kuzu");
const { Database, Connection } = kuzu;

export class KuzuSyncClient {
  private db: Database;
  private conn: Connection;
  private ws: WebSocket | null = null;
  private clientId: string;
  private reconnectTimer?: Timer;

  constructor(clientId?: string) {
    this.clientId = clientId || `bun_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    this.db = new Database(":memory:");
    this.conn = new Connection(this.db);
  }

  async initialize(): Promise<void> {
    // Create local schema (same as Deno version)
    await this.conn.query(`
      CREATE NODE TABLE LocalEvent(
        id STRING,
        template STRING,
        params STRING,
        timestamp INT64,
        synced BOOLEAN,
        PRIMARY KEY(id)
      )
    `);
    console.log(`[${this.clientId}] Local database initialized`);
  }

  connect(url: string = "ws://localhost:8080"): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${url}?clientId=${this.clientId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`[${this.clientId}] Connected to server`);
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error(`[${this.clientId}] WebSocket error:`, error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log(`[${this.clientId}] Disconnected, will reconnect...`);
        this.scheduleReconnect(url);
      };

      this.ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          await this.handleServerMessage(data);
        } catch (error) {
          console.error(`[${this.clientId}] Error handling message:`, error);
        }
      };
    });
  }

  private scheduleReconnect(url: string): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.reconnectTimer = setTimeout(() => {
      console.log(`[${this.clientId}] Attempting to reconnect...`);
      this.connect(url).catch(console.error);
    }, 5000);
  }

  private async handleServerMessage(data: any): Promise<void> {
    if (data.type === "event" && data.clientId !== this.clientId) {
      // Store remote event
      await this.storeEvent(data, true);
    }
  }

  async sendEvent(template: string, params: any): Promise<void> {
    const event = {
      type: "event",
      id: `${this.clientId}_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      template,
      params,
      clientId: this.clientId,
      timestamp: Date.now()
    };

    // Store locally first
    await this.storeEvent(event, false);

    // Send to server if connected
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(event));
      console.log(`[${this.clientId}] Sent: ${template}`);
    } else {
      console.warn(`[${this.clientId}] Not connected, event queued locally`);
    }
  }

  private async storeEvent(event: any, synced: boolean): Promise<void> {
    await this.conn.query(`
      CREATE (:LocalEvent {
        id: $id,
        template: $template,
        params: $params,
        timestamp: $timestamp,
        synced: $synced
      })
    `, {
      id: event.id,
      template: event.template,
      params: JSON.stringify(event.params),
      timestamp: event.timestamp || Date.now(),
      synced
    });
  }

  async getLocalEvents(limit: number = 10): Promise<any[]> {
    const result = await this.conn.query(`
      MATCH (e:LocalEvent)
      RETURN e.id, e.template, e.params, e.timestamp, e.synced
      ORDER BY e.timestamp DESC
      LIMIT $limit
    `, { limit });

    const events = [];
    while (result.hasNext()) {
      const row = result.getNext();
      events.push({
        id: row[0],
        template: row[1],
        params: JSON.parse(row[2]),
        timestamp: row[3],
        synced: row[4]
      });
    }
    return events;
  }

  close(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
    }
    this.conn.close();
    console.log(`[${this.clientId}] Client closed`);
  }
}

// Export for both Bun and Deno compatibility
export default KuzuSyncClient;