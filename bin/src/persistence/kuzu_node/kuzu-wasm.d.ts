declare module 'kuzu-wasm' {
  export class Database {
    constructor(path: string, bufferSize?: number);
    close(): Promise<void>;
  }

  export class Connection {
    constructor(database: Database, numThreads?: number);
    execute(query: string): Promise<any>;
    query(query: string): Promise<any>;
    close(): Promise<void>;
  }

  const kuzu: {
    Database: typeof Database;
    Connection: typeof Connection;
  };

  export default kuzu;
}

declare module 'kuzu-wasm/nodejs' {
  export * from 'kuzu-wasm';
}

declare module 'kuzu-wasm/sync' {
  export * from 'kuzu-wasm';
}

declare module 'kuzu-wasm/multithreaded' {
  export * from 'kuzu-wasm';
}