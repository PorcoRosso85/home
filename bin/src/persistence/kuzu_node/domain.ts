/**
 * Domain: Pure KuzuDB operations
 */

export type QueryResult = {
  getAllObjects: () => Promise<any[]>;
  toString: () => Promise<string>;
  close: () => Promise<void>;
};

export type Connection = {
  query: (cypher: string) => Promise<QueryResult>;
  close: () => Promise<void>;
};

export type Database = {
  close: () => Promise<void>;
};

/**
 * 単一クエリの実行
 */
export async function executeQuery(conn: Connection, cypher: string): Promise<any[]> {
  const result = await conn.query(cypher);
  const data = await result.getAllObjects();
  await result.close();
  return data;
}

/**
 * 複数クエリの順次実行
 */
export async function executeQueries(
  conn: Connection,
  queries: string[]
): Promise<void> {
  for (const query of queries) {
    const result = await conn.query(query);
    await result.close();
  }
}

/**
 * クエリ実行して最初の結果を取得
 */
export async function queryOne(
  conn: Connection,
  query: string
): Promise<any | null> {
  const results = await executeQuery(conn, query);
  return results.length > 0 ? results[0] : null;
}

/**
 * トランザクション操作
 */
export async function beginTransaction(conn: Connection): Promise<void> {
  const result = await conn.query('BEGIN TRANSACTION');
  await result.close();
}

export async function commitTransaction(conn: Connection): Promise<void> {
  const result = await conn.query('COMMIT');
  await result.close();
}

export async function rollbackTransaction(conn: Connection): Promise<void> {
  const result = await conn.query('ROLLBACK');
  await result.close();
}

/**
 * スキーマ作成のヘルパー
 */
export async function createSchema(
  conn: Connection,
  statements: string[]
): Promise<void> {
  console.log('📊 Creating schema...');
  for (const statement of statements) {
    if (statement.trim()) {
      console.log(`  Executing: ${statement}`);
      const result = await conn.query(statement);
      await result.close();
    }
  }
}

/**
 * データロードのヘルパー
 */
export async function loadData(
  conn: Connection,
  statements: string[]
): Promise<void> {
  console.log('📥 Loading data...');
  await executeQueries(conn, statements.filter(s => s.trim()));
}