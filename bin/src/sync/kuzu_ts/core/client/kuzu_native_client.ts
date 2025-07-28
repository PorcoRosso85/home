/**
 * KuzuDB Native Client - TypeScript Interface
 * Pythonネイティブクライアントへのインターフェース
 * 
 * Uses subprocess to communicate with Python KuzuDB client,
 * enabling actual DML execution unlike WASM implementation.
 */

import type { KuzuWasmClient, LocalState, EventSnapshot } from "../../types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";
import type { DDLTemplateEvent } from "../../event_sourcing/ddl_types.ts";
import { isDDLEvent, DDLOperationType } from "../../event_sourcing/ddl_types.ts";
import { createTemplateEvent, validateParams } from "../../event_sourcing/core.ts";
import { TemplateRegistry } from "../../event_sourcing/template_event_store.ts";
import { StateCache } from "../cache/state_cache.ts";
import { SchemaManager } from "../schema_manager.ts";
import { ExtendedTemplateRegistry } from "../../event_sourcing/ddl_event_handler.ts";
import * as telemetry from "../../telemetry_log.ts";

interface PythonResponse {
  success?: boolean;
  error?: string;
  state?: LocalState;
  result?: any;
  message?: string;
  traceback?: string;
}

export class KuzuNativeClientImpl implements KuzuWasmClient {
  private process?: Deno.ChildProcess;
  private writer?: WritableStreamDefaultWriter<string>;
  private reader?: ReadableStreamDefaultReader<Uint8Array>;
  private decoder = new TextDecoder();
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private extendedRegistry = new ExtendedTemplateRegistry();
  private clientId = `native_${crypto.randomUUID()}`;
  private stateCache = new StateCache();
  private schemaManager: SchemaManager;
  private initialized = false;

  constructor() {
    this.schemaManager = new SchemaManager(this.clientId);
  }

  async initialize(): Promise<void> {
    telemetry.info("Initializing native KuzuDB client", {
      clientId: this.clientId
    });

    // Start Python subprocess
    // Use the Python environment from Nix that includes kuzu
    const pythonPath = Deno.env.get("PYTHON_PATH") || "python";
    const scriptPath = new URL("kuzu_native_client.py", import.meta.url).pathname;
    
    telemetry.debug("Starting Python subprocess", {
      pythonPath,
      scriptPath,
      clientId: this.clientId
    });
    
    const command = new Deno.Command(pythonPath, {
      args: [scriptPath],
      stdin: "piped",
      stdout: "piped",
      stderr: "piped",
    });

    this.process = command.spawn();
    
    // Get the writer for stdin as text
    const textEncoder = new TextEncoderStream();
    textEncoder.readable.pipeTo(this.process.stdin);
    this.writer = textEncoder.writable.getWriter();
    
    // Set up stdout reader
    this.reader = this.process.stdout.getReader();
    
    // Set up stderr reader for logging
    const stderrReader = this.process.stderr.getReader();
    this.startStderrReader(stderrReader, this.decoder);
    
    // Send initialization request
    const initRequest = {
      method: "initialize",
      params: {}
    };
    
    await this.sendRequest(initRequest);
    const response = await this.readResponse(this.reader, this.decoder);
    
    if (response.error) {
      throw new Error(`Failed to initialize KuzuDB: ${response.error}`);
    }
    
    this.initialized = true;
    telemetry.info("Native KuzuDB client initialized successfully");
  }
  
  private async sendRequest(request: any): Promise<void> {
    if (!this.writer) {
      throw new Error("Client not initialized");
    }
    
    const data = JSON.stringify(request) + "\n";
    await this.writer.write(data);
  }
  
  private async readResponse(reader: ReadableStreamDefaultReader<Uint8Array>, decoder: TextDecoder): Promise<PythonResponse> {
    let buffer = "";
    
    // Read until we get a complete line
    while (true) {
      const { value, done } = await reader.read();
      
      if (done) {
        throw new Error("Python process terminated unexpectedly");
      }
      
      buffer += decoder.decode(value, { stream: true });
      
      // Check if we have a complete line
      const newlineIndex = buffer.indexOf('\n');
      if (newlineIndex !== -1) {
        const line = buffer.substring(0, newlineIndex).trim();
        
        // Keep remaining data in buffer
        buffer = buffer.substring(newlineIndex + 1);
        
        if (line) {
          try {
            return JSON.parse(line);
          } catch (e) {
            telemetry.error("Failed to parse response", { line, error: String(e) });
            throw new Error(`Invalid JSON response: ${line}`);
          }
        }
      }
    }
  }
  
  private startStderrReader(reader: ReadableStreamDefaultReader<Uint8Array>, decoder: TextDecoder): void {
    const readStderr = async () => {
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          const text = decoder.decode(value);
          const lines = text.trim().split('\n');
          
          for (const line of lines) {
            if (line.trim()) {
              try {
                const logEntry = JSON.parse(line);
                // Forward Python logs to our telemetry
                if (logEntry.level && logEntry.message) {
                  telemetry.log(logEntry.level.toLowerCase(), {
                    source: "python_native_client",
                    ...logEntry
                  });
                }
              } catch {
                // Not JSON, just log as debug
                telemetry.debug("Python stderr output", { output: line });
              }
            }
          }
        }
      } catch (error) {
        telemetry.error("Error reading stderr", { error: String(error) });
      }
    };
    
    readStderr();
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    await this.initialize();
    
    // Clear existing state
    this.events = [];
    this.stateCache.clear();
    
    // Initialize schema manager from snapshot
    await this.schemaManager.initializeFromSnapshot(
      snapshot.events,
      (query: string) => this.executeQuery(query)
    );
    
    // Replay all events from snapshot
    telemetry.info("Replaying events from snapshot", { count: snapshot.events.length });
    for (const event of snapshot.events) {
      await this.applyEvent(event);
      this.events.push(event);
    }
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    if (!this.initialized || !this.process) {
      throw new Error("Client not initialized");
    }
    
    // Check if this is a DDL template
    if (this.extendedRegistry.isDDLTemplate(template)) {
      // Create DDL event
      const ddlEvent = this.schemaManager.createDDLEvent(
        template as DDLOperationType,
        params
      );
      
      // Apply DDL event
      await this.applyEvent(ddlEvent);
      
      // Store event
      this.events.push(ddlEvent);
      
      return ddlEvent;
    }
    
    // For DML templates, use extended registry for validation
    const metadata = this.extendedRegistry.getTemplateMetadata(template);
    const sanitizedParams = validateParams(params, metadata);
    
    // Check for injection attempts
    for (const value of Object.values(sanitizedParams)) {
      if (typeof value === 'string' && 
          (value.includes("DROP") || value.includes("DELETE") || value.includes("--"))) {
        throw new Error("Invalid parameter: potential injection attempt");
      }
    }
    
    // Create event
    const event = createTemplateEvent(template, sanitizedParams, this.clientId);
    
    // Execute via Python subprocess
    const request = {
      method: "executeTemplate",
      params: {
        template: template,
        params: sanitizedParams
      }
    };
    
    await this.sendRequest(request);
    const response = await this.readResponse(this.reader!, this.decoder);
    
    if (response.error) {
      throw new Error(`Failed to execute template: ${response.error}`);
    }
    
    // Store event
    this.events.push(event);
    
    // Invalidate cache after applying new event
    this.stateCache.invalidateOnEvent(event);
    
    telemetry.info("Template executed via native client", {
      template,
      eventId: event.id,
      clientId: this.clientId
    });
    
    return event;
  }

  async getLocalState(): Promise<LocalState> {
    if (!this.initialized || !this.process) {
      return { users: [], posts: [], follows: [] };
    }
    
    // Check cache first for O(1) access
    const cachedState = this.stateCache.getCachedState();
    if (cachedState) {
      return cachedState;
    }
    
    try {
      const request = {
        method: "getLocalState",
        params: {}
      };
      
      await this.sendRequest(request);
      const decoder = new TextDecoder();
      const reader = this.process.stdout.getReader();
      const response = await this.readResponse(reader, decoder);
      
      if (response.error) {
        throw new Error(`Failed to get state: ${response.error}`);
      }
      
      const state = response.state || { users: [], posts: [], follows: [] };
      
      // Cache the computed state
      this.stateCache.setCachedState(state);
      
      return state;
    } catch (error) {
      telemetry.error("Error getting local state", { 
        error: String(error),
        clientId: this.clientId 
      });
      return { users: [], posts: [], follows: [] };
    }
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    if (!this.initialized) {
      throw new Error("Client not initialized");
    }
    
    // For DDL queries, execute directly via Python
    // This is used by SchemaManager
    const request = {
      method: "executeQuery",
      params: {
        query: cypher,
        params: params || {}
      }
    };
    
    await this.sendRequest(request);
    const response = await this.readResponse(this.reader!, this.decoder);
    
    if (response.error) {
      throw new Error(`Query execution failed: ${response.error}`);
    }
    
    return response.result;
  }

  async applyEvent(event: TemplateEvent | DDLTemplateEvent): Promise<void> {
    if (!this.initialized || !this.process) {
      throw new Error("Client not initialized");
    }

    // Check if it's a DDL event
    if (isDDLEvent(event)) {
      try {
        await this.schemaManager.applyDDLEvent(
          event,
          (query: string) => this.executeQuery(query)
        );
        // Notify handlers
        this.remoteEventHandlers.forEach(handler => handler(event));
      } catch (error) {
        telemetry.error(`Failed to apply DDL event ${event.id}`, { 
          error: String(error),
          clientId: this.clientId 
        });
        throw error; // DDL errors should propagate
      }
      return;
    }

    // For DML events, execute via Python
    const request = {
      method: "executeTemplate",
      params: {
        template: event.template,
        params: event.params
      }
    };
    
    await this.sendRequest(request);
    const response = await this.readResponse(this.reader!, this.decoder);
    
    if (response.error) {
      telemetry.error("Failed to apply event", {
        eventId: event.id,
        template: event.template,
        error: response.error,
        clientId: this.clientId
      });
      // Continue processing other events
    } else {
      // Invalidate cache since state has changed
      this.stateCache.invalidateOnEvent(event);
      
      // Notify handlers
      this.remoteEventHandlers.forEach(handler => handler(event));
    }
  }
  
  // Query counter value
  async queryCounter(counterId: string): Promise<number> {
    if (!this.initialized || !this.process) {
      throw new Error("Client not initialized");
    }
    
    const request = {
      method: "executeTemplate",
      params: {
        template: "QUERY_COUNTER",
        params: { counterId }
      }
    };
    
    await this.sendRequest(request);
    const response = await this.readResponse(this.reader!, this.decoder);
    
    if (response.error) {
      throw new Error(`Failed to query counter: ${response.error}`);
    }
    
    return response.result || 0;
  }

  // Schema query methods
  getSchemaVersion(): number {
    return this.schemaManager.getSchemaVersion();
  }

  getSchemaState() {
    return this.schemaManager.getCurrentSchema();
  }

  hasTable(tableName: string): boolean {
    return this.schemaManager.hasTable(tableName);
  }

  hasColumn(tableName: string, columnName: string): boolean {
    return this.schemaManager.hasColumn(tableName, columnName);
  }

  getTableSchema(tableName: string) {
    return this.schemaManager.getTableSchema(tableName);
  }

  getSchemaSyncState() {
    return this.schemaManager.getSyncState();
  }

  async resolveSchemaConflict(
    conflictId: string,
    resolution: "APPLY_FIRST" | "APPLY_LAST" | "MANUAL"
  ): Promise<void> {
    await this.schemaManager.resolveConflict(
      conflictId,
      resolution,
      (query: string) => this.executeQuery(query)
    );
  }

  // DDL Event Creation
  createDDLEvent(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): DDLTemplateEvent {
    return this.schemaManager.createDDLEvent(ddlType, params);
  }

  async applyDDLEvent(event: DDLTemplateEvent): Promise<void> {
    await this.applyEvent(event);
  }

  getAppliedDDLs(): DDLTemplateEvent[] {
    return this.schemaManager.getAppliedDDLs();
  }

  getPendingDDLs(): DDLTemplateEvent[] {
    return this.schemaManager.getPendingDDLs();
  }

  validateDDL(event: DDLTemplateEvent): { valid: boolean; errors: string[] } {
    return this.schemaManager.validateDDL(event);
  }

  // Template Support
  hasTemplate(template: string): boolean {
    return this.extendedRegistry.hasTemplate(template);
  }

  isDDLTemplate(template: string): boolean {
    return this.extendedRegistry.isDDLTemplate(template);
  }

  isDMLTemplate(template: string): boolean {
    return this.extendedRegistry.isDMLTemplate(template);
  }

  getTemplateMetadata(template: string): any {
    return this.extendedRegistry.getTemplateMetadata(template);
  }
  
  // Cleanup
  async close(): Promise<void> {
    if (this.process) {
      try {
        // Close stdin to signal shutdown
        await this.writer?.close();
        
        // Kill the process
        this.process.kill();
        
        // Wait for process to exit
        await this.process.status;
        
        telemetry.info("Native KuzuDB client closed", {
          clientId: this.clientId
        });
      } catch (error) {
        telemetry.error("Error closing native client", {
          error: String(error),
          clientId: this.clientId
        });
      }
    }
  }
}