import { Database, Connection } from "kuzu";

export interface DatabaseOptions {
  useCache?: boolean;
  testUnique?: boolean;
}

const dbCache = new Map<string, Database>();

export async function createDatabase(
  path: string,
  options: DatabaseOptions = {}
): Promise<Database> {
  const { useCache = true, testUnique = false } = options;
  
  // In-memory with testUnique should always create new instance
  if (path === ":memory:" && testUnique) {
    return new Database(":memory:");
  }
  
  // Check cache
  if (useCache && dbCache.has(path)) {
    return dbCache.get(path)!;
  }
  
  // Create new database
  const db = new Database(path);
  
  // Cache if enabled
  if (useCache) {
    dbCache.set(path, db);
  }
  
  return db;
}

export async function createConnection(db: Database): Promise<Connection> {
  return new Connection(db);
}

export function clearCache(): void {
  dbCache.clear();
}