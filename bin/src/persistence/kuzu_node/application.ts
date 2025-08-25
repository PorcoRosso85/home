/**
 * Application: Use cases for KuzuDB
 */

import { loadKuzu, createKuzuDatabase, cleanupKuzu, type DatabaseConfig } from './infrastructure';
import { 
  executeQuery, 
  executeQueries,
  queryOne,
  createSchema,
  loadData,
  beginTransaction,
  commitTransaction,
  rollbackTransaction
} from './domain';

/**
 * インメモリデータベースでのサンプル実行
 */
export async function runInMemoryExample() {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);

  // Schema
  await executeQueries(conn, [
    "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))"
  ]);
  
  // Data
  await executeQueries(conn, [
    "CREATE (:Person {name: 'Alice', age: 30})",
    "CREATE (:Person {name: 'Bob', age: 25})"
  ]);
  
  // Query
  const results = await executeQuery(conn, 
    "MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age"
  );
  
  // Cleanup
  await cleanupKuzu({ conn, db, kuzu });
  
  return results;
}

/**
 * 映画データベースのサンプル
 */
export async function runMovieExample(config?: DatabaseConfig) {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu, config);
  
  try {
    // スキーマ作成
    await createSchema(conn, [
      "CREATE NODE TABLE Movie(title STRING, year INT64, rating DOUBLE, PRIMARY KEY(title))",
      "CREATE NODE TABLE Actor(name STRING, age INT64, PRIMARY KEY(name))",
      "CREATE REL TABLE ActsIn(FROM Actor TO Movie, role STRING)"
    ]);

    // データロード
    await loadData(conn, [
      "CREATE (:Movie {title: 'The Matrix', year: 1999, rating: 8.7})",
      "CREATE (:Movie {title: 'Inception', year: 2010, rating: 8.8})",
      "CREATE (:Actor {name: 'Keanu Reeves', age: 59})",
      "CREATE (:Actor {name: 'Leonardo DiCaprio', age: 49})",
      "MATCH (a:Actor {name: 'Keanu Reeves'}), (m:Movie {title: 'The Matrix'}) CREATE (a)-[:ActsIn {role: 'Neo'}]->(m)",
      "MATCH (a:Actor {name: 'Leonardo DiCaprio'}), (m:Movie {title: 'Inception'}) CREATE (a)-[:ActsIn {role: 'Cobb'}]->(m)"
    ]);

    // クエリ実行
    const results = await executeQuery(conn, `
      MATCH (a:Actor)-[r:ActsIn]->(m:Movie)
      RETURN a.name as actor, r.role as role, m.title as movie, m.year as year
      ORDER BY m.year DESC
    `);

    // 統計情報
    const stats = await queryOne(conn, `
      MATCH (m:Movie)
      RETURN count(*) as totalMovies, avg(m.rating) as avgRating
    `);

    return { results, stats };
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
}

/**
 * トランザクションのサンプル
 */
export async function runTransactionExample() {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    // スキーマ作成
    await createSchema(conn, [
      "CREATE NODE TABLE Account(id INT64, balance DOUBLE, PRIMARY KEY(id))"
    ]);

    // 初期データ
    await loadData(conn, [
      "CREATE (:Account {id: 1, balance: 1000.0})",
      "CREATE (:Account {id: 2, balance: 500.0})"
    ]);

    // トランザクション開始
    await beginTransaction(conn);
    
    try {
      // 送金操作
      await executeQueries(conn, [
        "MATCH (a:Account {id: 1}) SET a.balance = a.balance - 100",
        "MATCH (a:Account {id: 2}) SET a.balance = a.balance + 100"
      ]);
      
      // 残高確認
      const balance1 = await queryOne(conn, "MATCH (a:Account {id: 1}) RETURN a.balance as balance");
      const balance2 = await queryOne(conn, "MATCH (a:Account {id: 2}) RETURN a.balance as balance");
      
      if (balance1.balance < 0) {
        throw new Error("Insufficient funds");
      }
      
      // コミット
      await commitTransaction(conn);
      
      return { 
        success: true, 
        balances: { account1: balance1.balance, account2: balance2.balance }
      };
    } catch (error) {
      // ロールバック
      await rollbackTransaction(conn);
      throw error;
    }
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
}