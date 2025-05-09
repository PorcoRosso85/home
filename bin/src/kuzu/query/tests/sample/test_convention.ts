/**
 * 階層型トレーサビリティモデル - コーディング規約（CONVENTION）テスト
 * 
 * このファイルはCONVENTION規約の格納とクエリをテストし、YAMLファイルなしでも規約情報を管理できることを確認します。
 */

import { 
  createDatabase, 
  closeConnection 
} from "../services/databaseService.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { callNamedDql } from "../call_dql.ts";

// 結果フォーマッターはインポートできない場合は代替関数を定義
function formatQueryResult(result: any): string {
  if (!result) return "結果なし";
  
  try {
    return JSON.stringify(result, null, 2);
  } catch (e) {
    return `結果のフォーマットに失敗: ${e.message}`;
  }
}

// テスト用DBの名前
const TEST_DB_NAME = "convention_test_db";

// メイン実行関数
(async () => {
  console.log("===== コーディング規約（CONVENTION）テスト =====");
  
  // 初期化
  let db: any, conn: any;
  
  try {
    // 1. データベースセットアップ
    console.log("\n1. データベースセットアップ");
    const result = await createDatabase(TEST_DB_NAME);
    db = result.db;
    conn = result.conn;
    console.log("✓ データベースセットアップ完了");
    
    // 2. スキーマ定義
    console.log("\n2. スキーマ定義");
    await callDdl(conn, "schema.cypher");
    console.log("✓ スキーマ定義完了");
    
    // 3. テストデータ挿入
    console.log("\n3. テストデータ挿入");
    await callDml(conn, "sample_data.cypher");
    console.log("✓ 基本テストデータ挿入完了");
    
    // 3.1 規約データの挿入
    console.log("\n3.1 規約データの挿入");
    await callDml(conn, "convention.cypher");
    console.log("✓ 規約データ挿入完了");
    
    // 4. CONVENTION規約データ確認
    console.log("\n4. CONVENTION規約データ確認");
    // 規約データが存在するか確認
    console.log("  規約データの確認...");
    const countResult = await conn.query(`
      MATCH (ref:ReferenceEntity)
      WHERE ref.type = 'CONVENTION_RULE'
      RETURN count(ref) AS rule_count
    `);
      
    countResult.resetIterator();
    const countRow = countResult.getNextSync();
    console.log(`  規約ルール数: ${countRow.rule_count}件`);
      
    if (countRow.rule_count === 0) {
      throw new Error("規約ルールがありません。先に規約ルールを作成してください。");
    }
      
    // 階層構造の確認
    const hierarchyResult = await conn.query(`
      MATCH (loc:LocationURI)
      WHERE loc.scheme = 'convention'
      RETURN count(loc) AS location_count
    `);
      
    hierarchyResult.resetIterator();
    const hierarchyRow = hierarchyResult.getNextSync();
    console.log(`  規約階層ノード数: ${hierarchyRow.location_count}件`);
      
    if (hierarchyRow.location_count === 0) {
      throw new Error("規約階層構造がありません。先に規約階層構造を作成してください。");
    }
      
    console.log("✓ 規約データ確認完了");
    
    // 5. すべての規約ルールを取得
    console.log("\n5. すべての規約ルールを取得");
    const rulesResult = await callNamedDql(conn, "convention.cypher", "get_all_convention_rules", {});
      
    console.log("  規約ルール一覧:");
    console.log("  ID | 説明 | タイプ | ソースタイプ");
    console.log("  ---|------|--------|------------");
      
    rulesResult.resetIterator();
    while (rulesResult.hasNext()) {
      const row = rulesResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.rule_type} | ${row.source_type}`);
    }
    
    // 6. 規約の階層構造を取得 - 簡略版
    console.log("\n6. 規約の階層構造を取得（簡略版）");
    const simpleHierarchyQuery = `
      MATCH (root:LocationURI {uri_id: 'convention:root'})
      MATCH (root)-[:CONTAINS_LOCATION]->(category:LocationURI)
      RETURN category.fragment AS category_name
      ORDER BY category.fragment
    `;
    
    const hierarchyResult2 = await conn.query(simpleHierarchyQuery);
    
    console.log("  規約階層構造（トップカテゴリのみ）:");
    
    hierarchyResult2.resetIterator();
    while (hierarchyResult2.hasNext()) {
      const row = hierarchyResult2.getNextSync();
      console.log(`  - ${row.category_name}`);
    }
    
    console.log("  ※階層構造の詳細取得は省略しました");

    
    // 7. カテゴリによる規約検索
    console.log("\n7. カテゴリによる規約検索");
    const categoryResult = await callNamedDql(conn, "convention.cypher", "get_rules_by_category", {
      category_name: "基本原則"
    });
      
    console.log("  「基本原則」カテゴリの規約:");
    console.log("  ID | 説明 | パス");
    console.log("  ---|------|----");
      
    categoryResult.resetIterator();
    while (categoryResult.hasNext()) {
      const row = categoryResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.full_path}`);
    }
    
    // 8. キーワードによる規約検索
    console.log("\n8. キーワードによる規約検索");
    const keywordResult = await callNamedDql(conn, "convention.cypher", "search_convention_by_keyword", {
      keyword: "TypedDict"
    });
      
    console.log("  「TypedDict」キーワードを含む規約:");
    console.log("  ID | 説明 | パス");
    console.log("  ---|------|----");
      
    keywordResult.resetIterator();
    while (keywordResult.hasNext()) {
      const row = keywordResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.rule_path}`);
    }
    
    // 9. サンプルコードと規約の関連付け
    console.log("\n9. サンプルコードと規約の関連付け");
    // サンプルコードの作成
    const codeResult = await conn.query(`
      CREATE (code:CodeEntity {
        persistent_id: 'sample_typed_dict_function',
        name: 'create_user_data',
        type: 'function',
        signature: 'def create_user_data(name: str, age: int) -> UserData:',
        complexity: 2,
        start_position: 120,
        end_position: 180
      })
      RETURN code.persistent_id AS code_id
    `);
      
    codeResult.resetIterator();
    const codeRow = codeResult.getNextSync();
    console.log(`  サンプルコード作成: ${codeRow.code_id}`);
      
    // コードと規約の関連付け
    const linkResult = await conn.query(`
      MATCH (code:CodeEntity {persistent_id: 'sample_typed_dict_function'}),
            (rule:ReferenceEntity {id: 'CONV_RULE_001'})
      CREATE (code)-[:REFERS_TO {ref_type: 'CONVENTION'}]->(rule)
      RETURN code.persistent_id AS code_id, rule.id AS rule_id
    `);

    linkResult.resetIterator();
    const linkRow = linkResult.getNextSync();
    console.log(`  コードと規約の関連付け: ${linkRow.code_id} -> ${linkRow.rule_id}`);
    
    // 10. コードが適用している規約を取得
    console.log("\n10. コードが適用している規約を取得");
    const codeConvResult = await callNamedDql(conn, "convention.cypher", "get_conventions_for_code", {
      code_id: "sample_typed_dict_function"
    });
    
    console.log("  サンプルコードが適用している規約:");
    console.log("  ID | 説明 | パス");
    console.log("  ---|------|----");
    
    codeConvResult.resetIterator();
    while (codeConvResult.hasNext()) {
      const row = codeConvResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.rule_path}`);
    }
    
    // 11. 規約が適用されているコードを取得
    console.log("\n11. 規約が適用されているコードを取得");
    const convCodeResult = await callNamedDql(conn, "convention.cypher", "get_code_using_convention", {
      rule_id: "CONV_RULE_001"
    });
    
    console.log("  TypedDict規約が適用されているコード:");
    console.log("  ID | 名前 | タイプ | 場所");
    console.log("  ---|------|--------|-----");
    
    convCodeResult.resetIterator();
    while (convCodeResult.hasNext()) {
      const row = convCodeResult.getNextSync();
      console.log(`  ${row.code_id} | ${row.code_name} | ${row.code_type} | ${row.code_location || '不明'}`);
    }
    
    // 12. 規約適用状況の集計
    console.log("\n12. 規約適用状況の集計");
    const usageResult = await callNamedDql(conn, "convention.cypher", "count_convention_usage", {});
    
    console.log("  規約の適用状況集計:");
    console.log("  ID | 説明 | 適用数");
    console.log("  ---|------|-------");
    
    usageResult.resetIterator();
    while (usageResult.hasNext()) {
      const row = usageResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.usage_count}`);
    }
    
    // 13. バージョン管理との連携
    console.log("\n13. バージョン管理との連携");
    const versionResult = await callNamedDql(conn, "convention.cypher", "get_convention_by_version", {
      version_id: "convention_v1.0.0"
    });
    
    console.log("  バージョン convention_v1.0.0 の規約:");
    console.log("  ID | 説明 | パス");
    console.log("  ---|------|----");
    
    versionResult.resetIterator();
    while (versionResult.hasNext()) {
      const row = versionResult.getNextSync();
      console.log(`  ${row.rule_id} | ${row.rule_description.substring(0, 50)}... | ${row.rule_path || '不明'}`);
    }
    
    // 14. 階層レベル別の規約集計
    console.log("\n14. 階層レベル別の規約集計");
    const levelResult = await callNamedDql(conn, "convention.cypher", "count_rules_by_level", {});
    
    console.log("  階層レベル別の規約数:");
    console.log("  レベル | ノード数");
    console.log("  ------|--------");
    
    // 累積データを手動で計算
    const levels: any[] = [];
    let cumulativeCount = 0;
    
    levelResult.resetIterator();
    while (levelResult.hasNext()) {
      const row = levelResult.getNextSync();
      levels.push(row);
    }
    
    // レベル順にソート
    levels.sort((a, b) => a.hierarchy_level - b.hierarchy_level);
    
    // 手動で累積カウントを計算して表示
    for (const row of levels) {
      if (row.hierarchy_level > 0) {
        cumulativeCount += row.locations;
      }
      console.log(`  ${row.hierarchy_level} | ${row.locations}`);
    }
    
    console.log(`  累積合計: ${cumulativeCount}`);
    
    
    // 15. 規約適用状況のサマリー
    console.log("\n15. 規約適用状況のサマリー");
    const summaryResult = await callNamedDql(conn, "convention.cypher", "get_convention_compliance_summary", {});
    
    summaryResult.resetIterator();
    const summaryRow = summaryResult.getNextSync();
    
    console.log("  規約適用状況サマリー:");
    console.log(`  総規約数: ${summaryRow.total_rules}件`);
    console.log(`  規約適用コード数: ${summaryRow.total_compliant_code}件`);
    console.log(`  未使用規約数: ${summaryRow.unused_rules}件 (${summaryRow.unused_percentage.toFixed(1)}%)`);
    console.log(`  未使用規約ID: ${summaryRow.unused_rule_ids.filter(Boolean).join(', ') || '(なし)'}`);
    
    
    console.log("\n===== テスト完了 =====");
    console.log("コーディング規約（CONVENTION）テストが完了しました。");
    console.log("CONVENTION.yamlの代わりにグラフDBで規約情報を管理できることが確認されました。");
    
  } catch (error) {
    console.error("\n===== テスト失敗 =====");
    console.error("テスト実行中にエラーが発生しました:");
    console.error(error);
  } finally {
    // 常にデータベース接続をクローズする
    if (db && conn) {
      console.log("\nデータベース接続をクローズしています...");
      try {
        await closeConnection(db, conn);
        console.log("データベース接続のクローズに成功しました");
      } catch (closeError) {
        console.error("データベース接続のクローズ中にエラーが発生しました:", closeError);
      }
    }
  }
})();