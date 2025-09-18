// Node.jsでCozoDBを使用する拡張実装
const { CozoDb } = require('cozo-node');
const path = require('path');
const fs = require('fs');

// 引数処理
const args = process.argv.slice(2);
const dbPath = args[0] || ':memory:'; // デフォルトはインメモリDB
const command = args[1] || 'demo';

// メイン関数
async function main() {
  try {
    console.log(`CozoDBを初期化中... (${dbPath})`);
    
    // DBインスタンスの作成
    const db = dbPath === ':memory:' ? new CozoDb() : new CozoDb(dbPath);
    console.log("CozoDBインスタンスが準備完了");

    // コマンド実行
    switch (command) {
      case 'demo':
        await runBasicDemo(db);
        break;
      case 'graph':
        await runGraphDemo(db);
        break;
      case 'vector':
        await runVectorSearchDemo(db);
        break;
      default:
        // カスタムクエリの実行
        if (command) {
          const result = await db.run(command);
          console.log(JSON.stringify(result, null, 2));
        } else {
          console.log("コマンドが指定されていません。'demo', 'graph', 'vector'のいずれかを指定してください。");
        }
    }

    // DBをクローズ
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

// 基本的なCRUDデモ
async function runBasicDemo(db) {
  console.log("=== 基本的なCRUDデモ ===");
  
  // リレーションを作成
  console.log("\nユーザーテーブルを作成:");
  await db.run(":create users {name: String, age: Int => email: String, active: Bool}");
  
  // データを挿入
  console.log("\nデータを挿入:");
  await db.run(`
    ?[name, age, email, active] <- [
      ['Alice', 30, 'alice@example.com', true],
      ['Bob', 25, 'bob@example.com', true],
      ['Charlie', 35, 'charlie@example.com', false]
    ];
    :put users {name, age => email, active}
  `);
  
  // データを取得
  console.log("\nすべてのユーザーを取得:");
  const users = await db.run("?[name, age, email, active] := *users{name, age, email, active}");
  console.log(JSON.stringify(users, null, 2));
  
  // 条件付きクエリ
  console.log("\nアクティブなユーザーのみ取得:");
  const activeUsers = await db.run("?[name, email] := *users{name, email, active: true}");
  console.log(JSON.stringify(activeUsers, null, 2));
  
  // データを更新
  console.log("\nAliceのメールアドレスを更新:");
  await db.run(`
    ?[name, age, email, active] <- [['Alice', 30, 'alice.new@example.com', true]];
    :put users {name, age => email, active}
  `);
  
  // 更新されたデータを確認
  console.log("\n更新後のデータ:");
  const updatedUsers = await db.run("?[name, age, email] := *users{name, age, email}");
  console.log(JSON.stringify(updatedUsers, null, 2));
  
  // データの削除
  console.log("\nBobを削除:");
  await db.run("?[name, age] <- [['Bob', 25]]; :rm users {name, age}");
  
  // 削除後のデータを確認
  console.log("\n削除後のデータ:");
  const afterDeleteUsers = await db.run("?[name, age, email] := *users{name, age, email}");
  console.log(JSON.stringify(afterDeleteUsers, null, 2));
}

// グラフデータベースデモ
async function runGraphDemo(db) {
  console.log("=== グラフデータベースデモ ===");
  
  // 人物ノードを作成
  console.log("\n人物ノードを作成:");
  await db.run(":create person {name: String => age: Int}");
  
  // 友人関係エッジを作成
  console.log("\n友人関係エッジを作成:");
  await db.run(":create friendship {person1: String, person2: String => since: Int}");
  
  // データを挿入
  console.log("\nデータを挿入:");
  await db.run(`
    ?[name, age] <- [
      ['Alice', 30],
      ['Bob', 25],
      ['Charlie', 35],
      ['David', 28],
      ['Eve', 22]
    ];
    :put person {name => age}
  `);
  
  await db.run(`
    ?[person1, person2, since] <- [
      ['Alice', 'Bob', 2020],
      ['Alice', 'Charlie', 2019],
      ['Bob', 'David', 2021],
      ['Charlie', 'Eve', 2018],
      ['David', 'Eve', 2022]
    ];
    :put friendship {person1, person2 => since}
  `);
  
  // 友人を取得
  console.log("\nAliceの友人を取得:");
  const aliceFriends = await db.run(`
    ?[friend_name, friend_age, since] := 
      *friendship{person1: 'Alice', person2: friend_name, since},
      *person{name: friend_name, age: friend_age}
  `);
  console.log(JSON.stringify(aliceFriends, null, 2));
  
  // 2ホップの友人関係を取得
  console.log("\nAliceの友人の友人を取得 (2ホップ):");
  const friendsOfFriends = await db.run(`
    // 直接の友人
    direct_friends[friend] := *friendship{person1: 'Alice', person2: friend};
    
    // 友人の友人 (Aliceと直接友人でない人)
    ?[fof_name, fof_age] := 
      direct_friends[direct_friend],
      *friendship{person1: direct_friend, person2: fof_name},
      *person{name: fof_name, age: fof_age},
      fof_name \!= 'Alice',
      not direct_friends[fof_name]
  `);
  console.log(JSON.stringify(friendsOfFriends, null, 2));
}

// ベクトル検索デモ
async function runVectorSearchDemo(db) {
  console.log("=== ベクトル検索デモ ===");
  
  // ドキュメントテーブルを作成
  console.log("\nドキュメントテーブルを作成:");
  await db.run(":create documents {id: String => title: String, content: String, embedding: <F32; 3>}");
  
  // データを挿入
  console.log("\nデータを挿入:");
  await db.run(`
    ?[id, title, content, embedding] <- [
      ['doc1', 'CozoDBの紹介', 'CozoDBはグラフデータベースの機能を備えた高性能なデータベースです。', [0.1, 0.2, 0.3]],
      ['doc2', 'Denoとは何か', 'DenoはTypeScriptのランタイムです。', [0.4, 0.5, 0.6]],
      ['doc3', 'Node.jsの使い方', 'Node.jsはサーバーサイドJavaScriptのランタイムです。', [0.7, 0.8, 0.9]],
      ['doc4', 'データベースの種類', 'リレーショナル、ドキュメント指向、グラフなど様々なデータベースがあります。', [0.2, 0.3, 0.4]]
    ];
    :put documents {id => title, content, embedding}
  `);
  
  // ベクトル検索インデックスを作成
  console.log("\nベクトル検索インデックスを作成:");
  await db.run(`
    ::hnsw create documents:vector_index {
      fields: [embedding],
      dim: 3,
      distance: Cosine
    }
  `);
  
  // ベクトル検索を実行
  console.log("\nベクトル検索を実行:");
  const vectorSearchResult = await db.run(`
    ?[score, id, title] := ~documents:vector_index{id, title | 
                                               query: [0.2, 0.3, 0.4], 
                                               bind_score: score,
                                               k: 2}
    :order -score
  `);
  console.log(JSON.stringify(vectorSearchResult, null, 2));
  
  // 全文検索インデックスを作成
  console.log("\n全文検索インデックスを作成:");
  await db.run(`
    ::fts create documents:text_index {
      extractor: content,
      tokenizer: Simple
    }
  `);
  
  // 全文検索を実行
  console.log("\n全文検索を実行:");
  const textSearchResult = await db.run(`
    ?[score, id, title, content] := ~documents:text_index{id, title, content | 
                                                      query: "データベース", 
                                                      bind_score: score}
    :order -score
  `);
  console.log(JSON.stringify(textSearchResult, null, 2));
}

// メイン処理の実行
main();
