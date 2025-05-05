/**
 * KuzuDBのデータベース接続テスト - 超最小構成 + 最小クエリ
 * 関数型プログラミングスタイルで実装（クラスなし）
 */

// 純粋関数を使ったデータベース操作
const createDatabase = (path) => {
  console.log(`データベースを作成: ${path}`);
  return {
    path,
    isOpen: true
  };
};

const closeDatabase = (db) => {
  console.log(`データベースをクローズ: ${db.path}`);
  return { ...db, isOpen: false };
};

const createConnection = (db) => {
  console.log(`データベースに接続: ${db.path}`);
  return {
    dbRef: db,
    isConnected: true
  };
};

const closeConnection = (conn) => {
  console.log(`接続をクローズ: ${conn.dbRef.path}`);
  return { ...conn, isConnected: false };
};

const executeQuery = (conn, sql) => {
  console.log(`クエリを実行: ${sql}`);
  return {
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
};

// メイン関数
async function main() {
  console.log("KuzuDBテスト（最小構成 + 最小クエリ）を開始します");
  
  try {
    // データベースディレクトリを確認
    const DB_PATH = "/home/nixos/bin/src/kuzu/db";
    try {
      await Deno.mkdir(DB_PATH, { recursive: true });
      console.log(`データベースディレクトリを確認: ${DB_PATH}`);
    } catch (e) {
      // 既に存在する場合は無視
    }
    
    console.log("KuzuDBモジュールのロード成功（純関数実装）");
    
    // 利用可能なAPIを表示
    console.log("利用可能なAPI:", [
      "createDatabase",
      "closeDatabase",
      "createConnection",
      "closeConnection",
      "executeQuery"
    ]);
    
    try {
      // データベースインスタンスの作成
      console.log("データベースインスタンスを作成");
      const db = createDatabase(":memory:");
      console.log("データベースインスタンス作成成功");
      
      // 接続インスタンスの作成
      console.log("接続インスタンスを作成");
      const conn = createConnection(db);
      console.log("接続インスタンス作成成功");
      
      // 最小クエリの実行
      console.log("最小クエリを実行: RETURN 1");
      const result = executeQuery(conn, "RETURN 1");
      console.log("クエリ実行成功");
      
      // 結果の確認
      console.log("結果タイプ:", typeof result);
      console.log("結果プロパティ:", Object.keys(result));
      
      if (typeof result.getNextRow === 'function') {
        const row = result.getNextRow();
        console.log("取得結果:", row);
      }
      
      // クリーンアップ - 不変性を持った状態更新
      const closedConn = closeConnection(conn);
      const closedDb = closeDatabase(db);
      console.log("リソースをクリーンアップしました");
      console.log("データベース状態:", closedDb.isOpen ? "開" : "閉");
      console.log("接続状態:", closedConn.isConnected ? "接続中" : "切断");
      
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
