// Kuzu-WASM初期化と実行
// Denoの標準的なインポート構文を使用し、WASMモジュールを適切に読み込む
import * as KuzuWasm from "npm:kuzu-wasm";

// NOTE: 元々は相対パスでのインポートを使用していました
// node_modulesからの相対パスに変更することでViteのWASMプラグインが正しく機能するようになっていましたが、
// 現在はoptimizeDepsの設定により、npm:プレフィックスを使用しても適切に動作します
// 旧: import * as KuzuWasm from "../node_modules/kuzu-wasm";

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
    
    // Kuzuモジュールの初期化
    appendOutput("KuzuWasmデフォルトエクスポート: " + typeof KuzuWasm.default);
    appendOutput("KuzuWasmモジュールキー: " + Object.keys(KuzuWasm).join(", "));
    
    // ESMとして正しくインポートするためのコード
    const kuzu = KuzuWasm.default || KuzuWasm;
    appendOutput("Kuzuインスタンス型: " + typeof kuzu);
    
    // DB初期化
    // メモリ内にDBを作成
    const db = new kuzu.Database("");
    appendOutput("データベースを作成しました");
    
    // 接続を作成
    const conn = new kuzu.Connection(db);
    
    appendOutput("データベースに接続しました");
    
    // CSVファイルの読み込み
    try {
      appendOutput("CSVファイルを読み込み中...");
      const response = await fetch('/remote_data.csv');
      const csvData = await response.text();
      appendOutput(`CSVデータ: ${csvData.substring(0, 100)}...`);
      
      // CSVをkuzu FS領域に書き込む
      if (kuzu.FS) {
        await kuzu.FS.writeFile("/remote_data.csv", csvData);
        appendOutput("CSVファイルをkuzu FSに書き込みました");
      } else {
        appendOutput("警告: kuzu.FSが利用できません。ファイルシステムアクセスをスキップします");
      }
    } catch (error) {
      appendOutput(`CSVファイル読み込みエラー: ${error.message}`);
    }
    
    // ユーザーテーブル作成
    try {
      const createUserTable = "CREATE NODE TABLE User(id INT64, name STRING, country STRING, PRIMARY KEY (id))";
      appendOutput(`クエリ実行: ${createUserTable}`);
      const createResult = await conn.query(createUserTable);
      appendOutput("テーブル作成完了");
      
      // CSVデータの読み込み（FSから）
      if (kuzu.FS) {
        const loadData = "COPY User FROM '/remote_data.csv'";
        appendOutput(`クエリ実行: ${loadData}`);
        const loadResult = await conn.query(loadData);
        appendOutput("データ読み込み完了");
      }
      
      // クエリ実行
      const query = "MATCH (a:User) RETURN a.*";
      appendOutput(`クエリ実行: ${query}`);
      const queryResult = await conn.query(query);
      
      // 結果の取得
      const allObjects = await queryResult.getAllObjects();
      appendOutput(`クエリ結果: ${JSON.stringify(allObjects, null, 2)}`);
      
      await queryResult.close();
    } catch (error) {
      appendOutput(`テーブル作成/クエリ実行エラー: ${error.message}`);
    }
    
    // クリーンアップ
    appendOutput("接続をクローズしています...");
    try {
      await conn.close();
      appendOutput("接続がクローズされました");
      
      await db.close();
      appendOutput("データベースがクローズされました");
    } catch (error) {
      appendOutput(`クリーンアップエラー: ${error.message}`);
    }
    
    appendOutput("デモ完了");
  } catch (error) {
    appendOutput(`エラー: ${error.message}`);
    console.error(error);
  }
}

// DOMが読み込まれたら実行
document.addEventListener("DOMContentLoaded", runKuzuDemo);
