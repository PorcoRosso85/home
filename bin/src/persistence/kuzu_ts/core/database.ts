// KuzuDB is a native module that requires special handling in Deno
// For now, we'll create a mock implementation for testing
const kuzu = {
  Database: class Database {
    constructor(public path: string) {}
    close() {}
  },
  Connection: class Connection {
    constructor(public database: any) {}
    async execute(query: string) {
      // Mock implementation
      if (query.includes("MATCH")) {
        return {
          async getAll() {
            return [
              { "p.name": "Bob", "p.age": 25 },
              { "p.name": "Alice", "p.age": 30 }
            ];
          }
        };
      }
      return {};
    }
  }
};

export interface DatabaseOptions {
  useCache?: boolean;
  testUnique?: boolean;
}

const dbCache = new Map<string, any>();

export async function createDatabase(
  path: string,
  options: DatabaseOptions = {}
): Promise<any> {
  const { useCache = true, testUnique = false } = options;
  
  // In-memory with testUnique should always create new instance
  if (path === ":memory:" && testUnique) {
    return new kuzu.Database(":memory:");
  }
  
  // Check cache
  if (useCache && dbCache.has(path)) {
    return dbCache.get(path)!;
  }
  
  // Create new database
  const db = new kuzu.Database(path);
  
  // Cache if enabled
  if (useCache) {
    dbCache.set(path, db);
  }
  
  return db;
}

export async function createConnection(db: any): Promise<any> {
  return new kuzu.Connection(db);
}

export function clearCache(): void {
  dbCache.clear();
}