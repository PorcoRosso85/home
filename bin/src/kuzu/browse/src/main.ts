// Kuzu-WASM初期化と実行
// 統一された初期化処理を使用して実装
import { 
  initializeDatabase, 
  setupUserTable, 
  isError, 
  loadCsvData, 
  cleanupDatabaseResources 
} from './infrastructure/database/databaseService';

console.log("Kuzu-WASM ESMモジュールを読み込みました");

// HTMLに出力する関数
const appendOutput = (text: string) => {
  const output = document.getElementById("output");
  if (output) {
    output.textContent += text + "\n";
  }
  console.log(text);
};

// メイン処理
async function runKuzuDemo() {
  try {
    appendOutput("Kuzu-Wasmを初期化中...");
    
    // 統一されたデータベース初期化処理
    const dbResult = await initializeDatabase();
    
    // エラーチェック
    if (isError(dbResult)) {
      appendOutput(`エラー: ${dbResult.message}`);
      return;
    }
    
    const { kuzu, db, conn } = dbResult;
    appendOutput("Kuzuインスタンス型: " + typeof kuzu);
    appendOutput("データベースを作成しました");
    appendOutput("データベースに接続しました");
    
    // ユーザーテーブルのセットアップ
    const setupError = await setupUserTable(conn);
    if (setupError) {
      appendOutput(`エラー: ${setupError.message}`);
      await cleanupDatabaseResources(conn, db);
      return;
    }
    
    // CSVファイルの読み込み
    const csvError = await loadCsvData(conn, kuzu);
    if (csvError) {
      appendOutput(`エラー: ${csvError.message}`);
      // フォールバック処理は禁止されているため、エラーが発生したら処理を中断
      await cleanupDatabaseResources(conn, db);
      return;
    }
    
    // クエリ実行
    try {
      const query = "MATCH (a:User) RETURN a.*";
      appendOutput(`クエリ実行: ${query}`);
      const queryResult = await conn.query(query);
      
      // 結果の取得（結果形式によって処理を分岐）
      let resultJson;
      if (queryResult.table) {
        // tableプロパティを持つ場合
        const resultTable = queryResult.table.toString();
        resultJson = JSON.parse(resultTable);
      } else if (queryResult.getAllObjects) {
        // getAllObjects()メソッドを持つ場合
        resultJson = await queryResult.getAllObjects();
      } else {
        // その他の場合はオブジェクトとして扱う
        resultJson = queryResult;
      }
      appendOutput(`クエリ結果: ${JSON.stringify(resultJson, null, 2)}`);
    } catch (error) {
      appendOutput(`クエリ実行エラー: ${error.message}`);
    }
    
    // クリーンアップ
    const cleanupError = await cleanupDatabaseResources(conn, db);
    if (cleanupError) {
      appendOutput(`クリーンアップ警告: ${cleanupError.message}`);
    } else {
      appendOutput("リソースを正常にクリーンアップしました");
    }
    
    appendOutput("デモ完了");
  } catch (error) {
    appendOutput(`エラー: ${error.message}`);
    console.error(error);
  }
}

// DOMが読み込まれたら実行
document.addEventListener("DOMContentLoaded", runKuzuDemo);
