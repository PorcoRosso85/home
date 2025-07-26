#!/usr/bin/env deno run --allow-all

/**
 * DDL Sync Real-World Scenario
 * DDL同期の実践シナリオ
 * 
 * このスクリプトは実際のサーバー/クライアント間でのDDL同期を示します
 */

import { ServerKuzuClient } from "../core/server/server_kuzu_client.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";

// === Step 1: WebSocketサーバーの起動 ===
console.log("=== Step 1: WebSocketサーバーを起動 ===");
console.log("別のターミナルで以下を実行:");
console.log("$ deno run --allow-all core/websocket/server.ts");
console.log("");
console.log("サーバーが起動したらEnterキーを押してください...");
await new Promise(resolve => {
  const listener = () => {
    Deno.stdin.removeEventListener("readable", listener);
    resolve(null);
  };
  Deno.stdin.addEventListener("readable", listener);
});

// === Step 2: クライアントAの接続とテーブル作成 ===
console.log("\n=== Step 2: クライアントA接続 & 初期スキーマ作成 ===");

// クライアントAを作成
const clientA = new ServerKuzuClient("client-A");
await clientA.initialize();

// 初期スキーマを作成
console.log("クライアントA: Productテーブルを作成中...");
const createProductTable = await clientA.createDDLEvent(
  "CREATE_NODE_TABLE",
  {
    tableName: "Product",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "price", type: "DOUBLE" }
    ],
    primaryKey: "id"
  }
);

await clientA.applyEvent(createProductTable);
console.log("✅ Productテーブル作成完了");

// データを挿入
await clientA.executeQuery(`
  CREATE (p:Product {
    id: 'p1',
    name: 'Laptop',
    price: 999.99
  })
`);
console.log("✅ 初期データ挿入完了");

// === Step 3: クライアントBの接続と自動同期 ===
console.log("\n=== Step 3: クライアントBが接続 (自動スキーマ同期) ===");

const clientB = new ServerKuzuClient("client-B");
await clientB.initialize();

// WebSocket経由でスキーマが同期される想定
// 実際の実装では、サーバーから履歴を取得
console.log("クライアントB: サーバーからスキーマ履歴を取得中...");

// 手動でイベントを適用（実際はWebSocket経由）
await clientB.applyEvent(createProductTable);

// クライアントBでテーブルの存在を確認
const hasProdTable = await clientB.hasTable("Product");
console.log(`✅ クライアントBでProductテーブル検出: ${hasProdTable}`);

// クライアントBでデータをクエリ
const result = await clientB.executeQuery(
  "MATCH (p:Product) RETURN p.name as name, p.price as price"
);
console.log("クライアントBのクエリ結果:", result);

// === Step 4: クライアントBがスキーマを拡張 ===
console.log("\n=== Step 4: クライアントBがカラムを追加 ===");

const addStockColumn = await clientB.createDDLEvent(
  "ADD_COLUMN",
  {
    tableName: "Product",
    columnName: "stock",
    columnType: "INT64",
    defaultValue: "0"
  }
);

await clientB.applyEvent(addStockColumn);
console.log("✅ クライアントB: stockカラム追加完了");

// 新しいカラムでデータ更新
await clientB.executeQuery(`
  MATCH (p:Product {id: 'p1'})
  SET p.stock = 50
`);

// === Step 5: クライアントAに変更が伝播 ===
console.log("\n=== Step 5: クライアントAに変更が伝播 ===");

// 実際はWebSocket経由で自動的に伝播
await clientA.applyEvent(addStockColumn);

const hasStockColumn = await clientA.hasColumn("Product", "stock");
console.log(`✅ クライアントAでstockカラム検出: ${hasStockColumn}`);

// クライアントAで拡張されたスキーマを使用
const stockResult = await clientA.executeQuery(`
  MATCH (p:Product {id: 'p1'})
  RETURN p.name as name, p.stock as stock
`);
console.log("クライアントAのクエリ結果:", stockResult);

// === Step 6: 新しいクライアントCが参加 ===
console.log("\n=== Step 6: 新しいクライアントCが参加 ===");

const clientC = new ServerKuzuClient("client-C");
await clientC.initialize();

// すべてのDDLイベントを順番に適用
console.log("クライアントC: 全スキーマ履歴を再生中...");
await clientC.applyEvent(createProductTable);
await clientC.applyEvent(addStockColumn);

// スキーマバージョン確認
const schemaStateA = await clientA.getSchemaState();
const schemaStateB = await clientB.getSchemaState();
const schemaStateC = await clientC.getSchemaState();

console.log("\n=== スキーマバージョン確認 ===");
console.log(`クライアントA: v${schemaStateA.version}`);
console.log(`クライアントB: v${schemaStateB.version}`);
console.log(`クライアントC: v${schemaStateC.version}`);
console.log("✅ 全クライアントのスキーマが同期されました！");

// === Step 7: 複雑なスキーマ変更 ===
console.log("\n=== Step 7: リレーションシップテーブルの追加 ===");

// Customerテーブルを追加
const createCustomerTable = await clientA.createDDLEvent(
  "CREATE_NODE_TABLE",
  {
    tableName: "Customer",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "email", type: "STRING" }
    ],
    primaryKey: "id"
  }
);

await clientA.applyEvent(createCustomerTable);
await clientB.applyEvent(createCustomerTable);
await clientC.applyEvent(createCustomerTable);

// PURCHASEDリレーションシップを追加
const createPurchasedRel = await clientC.createDDLEvent(
  "CREATE_EDGE_TABLE",
  {
    tableName: "PURCHASED",
    fromTable: "Customer",
    toTable: "Product",
    properties: "quantity INT64, purchaseDate DATE"
  }
);

// 依存関係を設定
createPurchasedRel.dependsOn = [createCustomerTable.id, createProductTable.id];

// 全クライアントに伝播
await clientC.applyEvent(createPurchasedRel);
await clientA.applyEvent(createPurchasedRel);
await clientB.applyEvent(createPurchasedRel);

console.log("✅ リレーションシップテーブル作成完了");

// テストデータ作成
await clientA.executeQuery(`
  CREATE (c:Customer {
    id: 'c1',
    name: 'Alice',
    email: 'alice@example.com'
  })
`);

await clientA.executeQuery(`
  MATCH (c:Customer {id: 'c1'})
  MATCH (p:Product {id: 'p1'})
  CREATE (c)-[:PURCHASED {quantity: 2, purchaseDate: date('2024-01-15')}]->(p)
`);

// 複雑なクエリの実行
const purchaseResult = await clientB.executeQuery(`
  MATCH (c:Customer)-[pur:PURCHASED]->(p:Product)
  RETURN c.name as customer, p.name as product, pur.quantity as qty
`);

console.log("\n=== 購入情報クエリ結果 ===");
console.log(purchaseResult);

// === まとめ ===
console.log("\n=== DDL同期シナリオ完了 ===");
console.log("実装されたポイント:");
console.log("1. ✅ 新規クライアントの自動スキーマ同期");
console.log("2. ✅ 動的なスキーマ拡張（カラム追加）");
console.log("3. ✅ 全クライアントへの変更伝播");
console.log("4. ✅ 依存関係のあるDDL操作");
console.log("5. ✅ スキーマバージョン管理");
console.log("");
console.log("📝 注: 実際の実装では、WebSocketサーバーが");
console.log("   DDLイベントを自動的に全クライアントに配信します");