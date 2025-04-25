import kuzu_wasm from "https://unpkg.com/@kuzu/kuzu-wasm@latest/dist/kuzu-browser.js";

let kuzu: any;
let db: any;
let conn: any;

// Kuzuを初期化する関数
async function initKuzu() {
  try {
    // Kuzuを初期化
    kuzu = await kuzu_wasm();
    console.log("Kuzu initialized");
    
    // インメモリデータベースを作成
    db = await kuzu.Database();
    conn = await kuzu.Connection(db);
    
    // サンプルデータを作成
    await conn.execute(`CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))`);
    await conn.execute(`CREATE (u:User {name: 'Alice', age: 35})`);
    await conn.execute(`CREATE (u:User {name: 'Bob', age: 42})`);
    
    console.log("Sample data created");
    
    // 出力エリアを更新
    document.getElementById("output").textContent = "データベースが初期化されました。クエリを実行してください。";
  } catch (error) {
    console.error("Error during initialization:", error);
    document.getElementById("output").textContent = `初期化エラー: ${error.message}`;
  }
}

// クエリを実行する関数
async function executeQuery(query: string) {
  try {
    if (!conn) {
      throw new Error("データベース接続が初期化されていません");
    }
    
    const result = await conn.execute(query);
    const resultJson = JSON.parse(result.table.toString());
    
    return resultJson;
  } catch (error) {
    console.error("Query execution error:", error);
    throw error;
  }
}

// ページ読み込み時の処理
document.addEventListener("DOMContentLoaded", () => {
  // 実行ボタンにイベントリスナーを追加
  const executeButton = document.getElementById("execute");
  executeButton.addEventListener("click", async () => {
    const queryTextarea = document.getElementById("query") as HTMLTextAreaElement;
    const outputElement = document.getElementById("output");
    
    try {
      const result = await executeQuery(queryTextarea.value);
      outputElement.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      outputElement.textContent = `クエリ実行エラー: ${error.message}`;
    }
  });
  
  // Kuzuを初期化
  initKuzu();
});
