/**
 * WebSocket Client with KuzuDB
 * Compatible with unified client interface
 */

// Using require() to load the packaged kuzu module
// This follows the Node.js compatible pattern
const kuzu = require("kuzu");
const { Database, Connection } = kuzu;

export interface ClientOptions {
  clientId?: string;
  dbPath?: string;  // Path for database storage
}

export class KuzuSyncClient {
  private db: Database;
  private conn: Connection;
  private ws: WebSocket | null = null;
  private clientId: string;
  private dbPath: string;
  private reconnectTimer?: Timer;

  constructor(options?: ClientOptions | string) {
    // Support both old string parameter and new options object
    if (typeof options === 'string') {
      this.clientId = options;
      this.dbPath = ":memory:";
    } else {
      this.clientId = options?.clientId || `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
      this.dbPath = options?.dbPath || ":memory:";
    }
    
    this.db = new Database(this.dbPath);
    this.conn = new Connection(this.db);
  }

  async initialize(): Promise<void> {
    // Check if table already exists for persistent databases
    try {
      const result = await this.conn.query("CALL show_tables() RETURN name");
      const tables = await result.getAll();
      const hasTable = tables.some(row => row.name === "LocalEvent");
      
      if (!hasTable) {
        // Create local schema
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
      } else {
        console.log(`[${this.clientId}] Using existing database`);
      }
    } catch (error) {
      // If show_tables fails, try to create the table anyway
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
  }

  connect(url: string = "ws://localhost:8080"): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${url}?clientId=${this.clientId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = async () => {
        console.log(`[${this.clientId}] Connected to server`);
        
        // Sync pending events
        await this.syncPendingEvents();
        
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
    if (data.type === "event") {
      const event = data.payload || data;
      
      // Only store events from other clients
      if (event.clientId !== this.clientId) {
        // Store remote event as synced
        await this.storeEvent(event, true);
        console.log(`[${this.clientId}] Received event: ${event.template} from ${event.clientId}`);
      }
    }
  }

  async syncPendingEvents(): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const unsynced = await this.getUnsyncedEvents();
    console.log(`[${this.clientId}] Syncing ${unsynced.length} pending events`);
    
    for (const event of unsynced) {
      // Resend the event
      this.ws.send(JSON.stringify({
        type: "event",
        id: event.id,
        template: event.template,
        params: event.params,
        clientId: this.clientId,
        timestamp: event.timestamp
      }));
      
      // Mark as synced
      await this.markEventSynced(event.id);
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
      
      // Mark as synced since we sent it
      await this.markEventSynced(event.id);
    } else {
      console.warn(`[${this.clientId}] Not connected, event queued locally`);
    }
  }

  private async storeEvent(event: any, synced: boolean): Promise<void> {
    // Embed parameters directly in query string for compatibility
    const paramsStr = JSON.stringify(event.params).replace(/'/g, "''");
    await this.conn.query(`
      CREATE (:LocalEvent {
        id: '${event.id}',
        template: '${event.template}',
        params: '${paramsStr}',
        timestamp: ${event.timestamp || Date.now()},
        synced: ${synced}
      })
    `);
  }

  async getLocalEvents(limit: number = 10): Promise<any[]> {
    // Embed parameter in query string (package limitation)
    const result = await this.conn.query(`
      MATCH (e:LocalEvent)
      RETURN e.id as id, e.template as template, e.params as params, e.timestamp as timestamp, e.synced as synced
      ORDER BY e.timestamp DESC
      LIMIT ${limit}
    `);

    // Use getAll() for compatibility
    const rows = await result.getAll();
    return rows.map(row => ({
      id: row.id,
      template: row.template,
      params: row.params ? JSON.parse(row.params) : {},
      timestamp: row.timestamp,
      synced: row.synced
    }));
  }

  async getUnsyncedEvents(limit: number = 100): Promise<any[]> {
    const result = await this.conn.query(`
      MATCH (e:LocalEvent)
      WHERE e.synced = false
      RETURN e.id as id, e.template as template, e.params as params, e.timestamp as timestamp, e.synced as synced
      ORDER BY e.timestamp ASC
      LIMIT ${limit}
    `);
    
    const rows = await result.getAll();
    return rows.map(row => ({
      id: row.id,
      template: row.template,
      params: row.params ? JSON.parse(row.params) : {},
      timestamp: row.timestamp,
      synced: row.synced
    }));
  }

  async markEventSynced(eventId: string): Promise<void> {
    await this.conn.query(`
      MATCH (e:LocalEvent {id: '${eventId}'})
      SET e.synced = true
    `);
  }

  close(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    if (this.ws) {
      // Prevent reconnection on intentional close
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
    this.conn.close();
    console.log(`[${this.clientId}] Client closed`);
  }
}

// Export for compatibility
export default KuzuSyncClient;