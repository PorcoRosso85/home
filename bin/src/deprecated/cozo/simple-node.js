// Node.jsでCozoDBを使用するシンプルな実装
const { CozoDb } = require('cozo-node');

// メイン関数
async function main() {
  try {
    // インメモリDBの作成
    const db = new CozoDb();
    console.log("CozoDBインスタンスが準備完了");

    // 基本的なクエリの実行
    async function runQuery(query, params = {}) {
      try {
        const result = await db.run(query, params);
        return result;
      } catch (error) {
        console.error("クエリ実行エラー:", error);
        return { error: error.message };
      }
    }

    // 簡単なクエリを実行
    console.log("基本クエリを実行:");
    const basic = await runQuery("?[] <- [['hello', 'world']]");
    console.log(JSON.stringify(basic, null, 2));

    // ユーザーテーブルを作成
    console.log("\nテーブルを作成:");
    await runQuery(":create users {name: String, age: Int}");

    // データを挿入
    console.log("\nデータを挿入:");
    await runQuery("?[name, age] <- [['Alice', 30], ['Bob', 25], ['Charlie', 35]]; :put users {name, age}");

    // データを取得
    console.log("\nデータを取得:");
    const users = await runQuery("?[name, age] := *users{name, age}");
    console.log(JSON.stringify(users, null, 2));

    // 条件付きクエリ
    console.log("\n30歳以上のユーザーを取得:");
    const over30 = await runQuery("?[name, age] := *users{name, age}, age >= 30");
    console.log(JSON.stringify(over30, null, 2));

    // DBをクローズ（最新のAPIでは.free()ではなくclose()を使用）
    if (typeof db.close === 'function') {
      await db.close();
    } else if (typeof db.free === 'function') {
      db.free();
    }
    console.log("\nCozoDBインスタンスを解放しました");
  } catch (error) {
    console.error("エラー:", error);
  }
}

// メイン処理の実行
main();
