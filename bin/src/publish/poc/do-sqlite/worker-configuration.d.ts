interface Env {
  SQLITE_DO: DurableObjectNamespace;
}

interface SqlStorage {
  exec(query: string, ...params: any[]): SqlStorageResult;
}

interface SqlStorageResult {
  toArray(): any[];
}

interface DurableObjectState {
  storage: {
    sql: SqlStorage;
  };
  blockConcurrencyWhile<T>(callback: () => Promise<T>): Promise<T>;
}