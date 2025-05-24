// 多粒度モデル用テストデータ作成
// 階層構造: Level1 -> Level2 -> Level3 -> Level4

// ノードテーブル作成
CREATE NODE TABLE Level1(name STRING, PRIMARY KEY (name));
CREATE NODE TABLE Level2(name STRING, PRIMARY KEY (name));
CREATE NODE TABLE Level3(name STRING, PRIMARY KEY (name));
CREATE NODE TABLE Level4(name STRING, PRIMARY KEY (name));

// 関係テーブル作成（一つのCONTAINSテーブルで全階層を統合）
CREATE REL TABLE CONTAINS(FROM Level1 TO Level2, FROM Level2 TO Level3, FROM Level3 TO Level4);

// テストデータ挿入（プライマリキーを明示的に指定）
CREATE (:Level1 {name: "srs"});
CREATE (:Level2 {name: "functions"});
CREATE (:Level3 {name: "authentication"});
CREATE (:Level4 {name: "user-credential-validation"});

// 関係作成
MATCH (srs:Level1 {name: "srs"}), (functions:Level2 {name: "functions"})
CREATE (srs)-[:CONTAINS]->(functions);

MATCH (functions:Level2 {name: "functions"}), (auth:Level3 {name: "authentication"})
CREATE (functions)-[:CONTAINS]->(auth);

MATCH (auth:Level3 {name: "authentication"}), (leaf:Level4 {name: "user-credential-validation"})
CREATE (auth)-[:CONTAINS]->(leaf);