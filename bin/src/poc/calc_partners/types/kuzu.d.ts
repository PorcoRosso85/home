declare module 'kuzu-wasm' {
  export interface KuzuDatabase {
    close(): Promise<void>;
  }

  export interface KuzuConnection {
    execute(query: string): Promise<KuzuQueryResult>;
    close(): Promise<void>;
  }

  export interface KuzuQueryResult {
    table: KuzuTable;  // Kuzu WASM 0.7.0では必須
    close(): Promise<void>;
  }

  export interface KuzuTable {
    toString(): string;
  }

  export interface KuzuModule {
    Database(databasePath?: string): Promise<KuzuDatabase>;
    Connection(database: KuzuDatabase): Promise<KuzuConnection>;
  }

  export interface KuzuInitOptions {
    /**
     * Path to the kuzu-wasm.wasm file
     */
    wasmPath?: string;
    /**
     * Number of threads to use
     */
    numThreads?: number;
  }

  /**
   * Initialize the Kuzu WASM module and return the module instance
   */
  export default function initKuzu(options?: KuzuInitOptions): Promise<KuzuModule>;
}

declare module '*.cypher' {
  const content: string;
  export default content;
}

declare module '*.cypher?raw' {
  const content: string;
  export default content;
}