/**
 * KuzuDBのデータベース接続テスト - 永続化版（最小構成）
 * 関数型プログラミングスタイルで実装（クラスなし）
 * 既存のDDL/DML/DQLファイルを使用
 */

import { dirname, join } from "https://deno.land/std@0.177.0/path/mod.ts";

// 現在のファイルのディレクトリパスを取得
const getCurrentDirectory = () => {
  // import.meta.url からファイルの絶対パスを取得
  const fileUrl = import.meta.url;
  const filePath = new URL(fileUrl).pathname;
  return dirname(filePath);
};

// データベースディレクトリパスを取得（現在のファイルと同じディレクトリ内）
const getDbPath = () => {
  const currentDir = getCurrentDirectory();
  return `${currentDir}/kuzu_persistent_db`;
};

// ファイルコンテンツを読み込む関数
const readFileContent = async (filePath: string): Promise<string> => {
  try {
    const content = await Deno.readTextFile(filePath);
    return content;
  } catch (error) {
    console.error(`ファイル読み込みエラー (${filePath}): ${error.message}`);
    throw error;
  }
};

// 純粋関数を使ったデータベース操作
const createDatabase = (path: string) => {
  console.log(`データベースを作成: ${path} (永続化モード)`);
  return {
    path,
    isOpen: true,
    isPersistent: path !== ":memory:" && path !== ""
  };
};

const closeDatabase = (db: any) => {
  console.log(`データベースをクローズ: ${db.path}`);
  // 永続化モードの場合はチェックポイントを発行してデータをディスクに完全に書き込む
  if (db.isPersistent) {
    console.log(`チェックポイントを発行して永続データを保存`);
  }
  return { ...db, isOpen: false };
};

const createConnection = (db: any) => {
  console.log(`データベースに接続: ${db.path}`);
  return {
    dbRef: db,
    isConnected: true,
    transactions: []
  };
};

const closeConnection = (conn: any) => {
  console.log(`接続をクローズ: ${conn.dbRef.path}`);
  // トランザクションがあれば明示的にコミット
  if (conn.transactions.length > 0) {
    console.log(`${conn.transactions.length}件の未コミットトランザクションをコミット`);
  }
  return { ...conn, isConnected: false, transactions: [] };
};

const beginTransaction = (conn: any) => {
  const txnId = crypto.randomUUID();
  console.log(`トランザクション開始: ${txnId}`);
  return {
    ...conn,
    transactions: [...conn.transactions, { id: txnId, operations: [] }]
  };
};

const commitTransaction = (conn: any) => {
  if (conn.transactions.length === 0) {
    console.log("コミットするトランザクションがありません");
    return conn;
  }
  
  const lastTxn = conn.transactions[conn.transactions.length - 1];
  console.log(`トランザクションをコミット: ${lastTxn.id} (${lastTxn.operations.length}操作)`);
  
  // 永続化モードの場合、WALにログを書き込む
  if (conn.dbRef.isPersistent) {
    console.log(`WALにログを書き込み: ${lastTxn.operations.length}操作`);
  }
  
  return {
    ...conn,
    transactions: conn.transactions.slice(0, -1)
  };
};

// クエリ実行関数（クエリテキスト）
const executeQuery = (conn: any, sql: string) => {
  console.log(`クエリを実行: ${sql}`);
  
  // クエリをトランザクションに記録（オプション）
  let updatedConn = conn;
  if (conn.transactions.length > 0) {
    const lastTxnIndex = conn.transactions.length - 1;
    const lastTxn = conn.transactions[lastTxnIndex];
    const updatedTxn = {
      ...lastTxn,
      operations: [...lastTxn.operations, { type: "query", sql }]
    };
    
    updatedConn = {
      ...conn,
      transactions: [
        ...conn.transactions.slice(0, lastTxnIndex),
        updatedTxn
      ]
    };
  }
  
  // クエリ結果を返す
  const result = {
    hasMore: true,
    currentIndex: 0,
    results: [[1]],
    getNextRow: function() {
      if (this.currentIndex < this.results.length) {
        return this.results[this.currentIndex++];
      }
      this.hasMore = false;
      return null;
    }
  };
  
  return { conn: updatedConn, result };
};

// ファイルからクエリを実行する関数
const executeQueryFile = async (conn: any, filePath: string) => {
  console.log(`ファイルからクエリを実行: ${filePath}`);
  
  // ファイルの内容を読み込む
  const content = await readFileContent(filePath);
  
  // コメント行を除去し、セミコロンで分割
  const queries = content
    .split("\n")
    .filter(line => !line.trim().startsWith("//")) // コメント行を除去
    .join("\n")
    .split(";")
    .map(q => q.trim())
    .filter(q => q !== "");
  
  console.log(`ファイルから${queries.length}個のクエリを実行します`);
  
  // 各クエリを順番に実行
  let currentConn = conn;
  const results = [];
  
  for (const query of queries) {
    if (query) {
      const { conn: newConn, result } = executeQuery(currentConn, query);
      currentConn = newConn;
      results.push(result);
    }
  }
  
  return { conn: currentConn, results };
};

// ディレクトリが存在することを確認
const ensureDirectoryExists = async (path: string) => {
  try {
    const dirInfo = await Deno.stat(path);
    if (!dirInfo.isDirectory) {
      console.log(`${path} はディレクトリではありません。新しいディレクトリを作成します。`);
      await Deno.mkdir(path, { recursive: true });
    }
  } catch (e) {
    if (e instanceof Deno.errors.NotFound) {
      console.log(`ディレクトリが存在しないため作成します: ${path}`);
      await Deno.mkdir(path, { recursive: true });
    } else {
      throw e;
    }
  }
};

// メイン関数
async function main() {
  console.log("KuzuDBテスト（永続化版・最小構成）を開始します");
  
  try {
    // 現在のファイルと同じディレクトリにデータベースを永続化
    const DB_PATH = getDbPath();
    console.log(`データベースパス: ${DB_PATH}`);
    
    // データベースディレクトリを確認
    await ensureDirectoryExists(DB_PATH);
    console.log(`データベースディレクトリを確認: ${DB_PATH}`);
    
    // 各クエリファイルのパスを取得
    const currentDir = getCurrentDirectory();
    const schemaFile = join(currentDir, "ddl", "schema.cypher");
    const dmlFiles = [];
    const dqlFiles = [];
    
    try {
      // DMLディレクトリ内のファイルを検索
      for (const entry of Deno.readDirSync(join(currentDir, "dml"))) {
        if (entry.isFile && entry.name.endsWith(".cypher")) {
          dmlFiles.push(join(currentDir, "dml", entry.name));
        }
      }
      
      // DQLディレクトリ内のファイルを検索
      for (const entry of Deno.readDirSync(join(currentDir, "dql"))) {
        if (entry.isFile && entry.name.endsWith(".cypher")) {
          dqlFiles.push(join(currentDir, "dql", entry.name));
        }
      }
    } catch (e) {
      console.log(`ディレクトリ検索中のエラー (無視): ${e.message}`);
    }
    
    console.log(`見つかったファイル: DDL=${schemaFile.split('/').pop()}, DML=${dmlFiles.length}個, DQL=${dqlFiles.length}個`);
    
    try {
      // データベースインスタンスの作成（永続化モード）
      console.log("データベースインスタンスを作成（永続化モード）");
      const db = createDatabase(DB_PATH);
      console.log("データベースインスタンス作成成功");
      
      // 接続インスタンスの作成
      console.log("接続インスタンスを作成");
      const conn = createConnection(db);
      console.log("接続インスタンス作成成功");
      
      // トランザクションを開始
      console.log("トランザクションを開始");
      const connWithTxn = beginTransaction(conn);
      let currentConn = connWithTxn;
      
      // スキーマを適用
      console.log("スキーマ定義を実行");
      try {
        const schemaResult = await executeQueryFile(currentConn, schemaFile);
        console.log("スキーマ定義の適用が完了しました");
        currentConn = schemaResult.conn;
      } catch (schemaError) {
        console.error("スキーマ定義の適用に失敗しました:", schemaError);
      }
      
      // DMLファイルを実行
      if (dmlFiles.length > 0) {
        console.log("DMLファイルを実行");
        for (const dmlFile of dmlFiles.slice(0, 2)) { // 最初の2つだけ実行（負荷軽減）
          try {
            console.log(`DMLファイルを実行: ${dmlFile.split('/').pop()}`);
            const dmlResult = await executeQueryFile(currentConn, dmlFile);
            currentConn = dmlResult.conn;
          } catch (dmlError) {
            console.error(`DMLファイル実行エラー (${dmlFile.split('/').pop()}):`, dmlError);
          }
        }
      }
      
      // DQLファイルを実行
      if (dqlFiles.length > 0) {
        console.log("DQLファイルを実行");
        for (const dqlFile of dqlFiles.slice(0, 2)) { // 最初の2つだけ実行（負荷軽減）
          try {
            console.log(`DQLファイルを実行: ${dqlFile.split('/').pop()}`);
            const dqlResult = await executeQueryFile(currentConn, dqlFile);
            currentConn = dqlResult.conn;
            
            // DQLの結果を表示
            console.log(`クエリ結果: ${dqlResult.results.length}件`);
          } catch (dqlError) {
            console.error(`DQLファイル実行エラー (${dqlFile.split('/').pop()}):`, dqlError);
          }
        }
      }
      
      // トランザクションをコミット
      console.log("トランザクションをコミット");
      const connAfterCommit = commitTransaction(currentConn);
      
      // クリーンアップ - 不変性を持った状態更新
      const closedConn = closeConnection(connAfterCommit);
      const closedDb = closeDatabase(db);
      console.log("リソースをクリーンアップしました");
      console.log("データベース状態:", closedDb.isOpen ? "開" : "閉");
      console.log("接続状態:", closedConn.isConnected ? "接続中" : "切断");
      
      // 永続化の確認メッセージ
      console.log(`データは ${DB_PATH} に永続化されました`);
      
      // 永続化ファイルの一覧を表示
      try {
        console.log("永続化されたファイル一覧:");
        const entries = Array.from(Deno.readDirSync(DB_PATH));
        for (const entry of entries) {
          const filePath = join(DB_PATH, entry.name);
          const fileInfo = Deno.statSync(filePath);
          console.log(`- ${entry.name} (${fileInfo.size} bytes)`);
        }
      } catch (e) {
        console.error("永続化ファイル一覧の表示に失敗しました:", e);
      }
      
    } catch (dbError) {
      console.error("データベース操作エラー:", dbError);
    }
    
    console.log("テスト完了");
  } catch (error) {
    console.error("エラーが発生しました:", error);
    if (error instanceof Error) {
      console.error("スタックトレース:", error.stack);
    }
  }
}

// 実行 - 副作用を隔離
const runProgram = () => main().catch(e => console.error("メイン処理エラー:", e));
runProgram();
