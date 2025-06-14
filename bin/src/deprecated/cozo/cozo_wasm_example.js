#!/usr/bin/env -S nix run nixpkgs#nodejs_22 --

/**
 * CozoDBのWasm版を試すシンプルなサンプル (Node.js 22用)
 * 
 * 注意: このスクリプトはCozoDB Wasm実装の基本的な構造を示すものです。
 */

// Node.jsのパス解決を使用して絶対パスでモジュールを読み込む
const path = require('path');
const fs = require('fs');
const modulePath = path.resolve(__dirname, 'node_modules/cozo-lib-wasm/cozo_lib_wasm.js');
console.log('Loading module from:', modulePath);

// WAMSファイルのパス確認
const wasmPath = path.resolve(__dirname, 'node_modules/cozo-lib-wasm/cozo_lib_wasm_bg.wasm');
console.log('WASM binary path:', wasmPath);
console.log('WASM binary exists:', fs.existsSync(wasmPath));

try {
  const cozoWasm = require(modulePath);
  
  // モジュール情報を表示
  console.log("Module exports:", Object.keys(cozoWasm));
  
  // ESMとCJSの違いを考慮したメソッド取得
  const init = cozoWasm.default || cozoWasm.init;
  const CozoDb = cozoWasm.CozoDb;
  
  console.log("Init function type:", typeof init);
  console.log("CozoDb type:", typeof CozoDb);
  
  if (typeof init !== 'function') {
    throw new Error("Initialization function not found");
  }
  
  if (typeof CozoDb !== 'function') {
    throw new Error("CozoDb class not found");
  }
  
  // デバッグ用に関数とクラスの詳細を表示
  if (typeof CozoDb === 'function') {
    console.log("CozoDb properties:", Object.getOwnPropertyNames(CozoDb));
    console.log("CozoDb prototype properties:", 
      Object.getOwnPropertyNames(CozoDb.prototype || {}));
  }
  
  // テスト関数
  async function testCozoDB() {
    console.log("\n--- STARTING COZO TESTS ---");
    
    try {
      // モジュール初期化
      console.log("1. Initializing WASM module...");
      await init();
      console.log("   ✓ Module initialized");
      
      // データベース作成
      console.log("2. Creating database instance...");
      const db = CozoDb.new();
      console.log("   ✓ Database created");
      
      // プロパティ確認
      console.log("   Database instance properties:", 
        Object.getOwnPropertyNames(db));
      console.log("   Database prototype properties:", 
        Object.getOwnPropertyNames(Object.getPrototypeOf(db) || {}));
      
      // リレーション作成
      if (typeof db.run === 'function') {
        console.log("3. Creating relation...");
        const createRelResult = db.run(":create rel people {name: String, age: Int64}");
        console.log("   Result:", createRelResult);
        
        // クリーンアップ
        console.log("4. Cleaning up...");
        if (typeof db.free === 'function') {
          db.free();
          console.log("   ✓ Database freed");
        } else {
          console.log("   ! No free method available");
        }
      } else {
        console.log("   ! No run method available on database instance");
      }
      
    } catch (error) {
      console.error("TEST ERROR:", error);
      console.error("Message:", error.message);
      console.error("Stack:", error.stack);
    }
    
    console.log("--- TESTS COMPLETED ---");
  }
  
  // テスト実行
  testCozoDB()
    .then(() => console.log("Tests finished successfully"))
    .catch(err => {
      console.error("Unhandled test error:", err);
      process.exit(1);
    });
    
} catch (loadError) {
  console.error("Failed to load module:", loadError);
  console.error("Stack trace:", loadError.stack);
}
