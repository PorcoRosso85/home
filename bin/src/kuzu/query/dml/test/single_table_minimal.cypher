// 8階層可変対応 1テーブル多粒度モデル（LocationURIのみ）
CREATE NODE TABLE LocationURI(id STRING, PRIMARY KEY (id));
CREATE REL TABLE PARENT_OF(FROM LocationURI TO LocationURI);

// 階層別テストデータ（配列範囲外を防ぐため個別処理）
// 2階層: /api/v1
WITH "/api/v1" as fullPath
WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts
MERGE (:LocationURI {id: "/" + parts[1]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
WITH parts
MATCH (p:LocationURI {id: "/" + parts[1]}), (c:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (p)-[:PARENT_OF]->(c);

// 3階層: /docs/guide/advanced
WITH "/docs/guide/advanced" as fullPath
WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts
MERGE (:LocationURI {id: "/" + parts[1]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
WITH parts
MATCH (p1:LocationURI {id: "/" + parts[1]}), (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (p1)-[:PARENT_OF]->(p2)
WITH parts
MATCH (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]}), (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (p2)-[:PARENT_OF]->(p3);

// 4階層: /srs/functions/authentication/user-credential-validation
WITH "/srs/functions/authentication/user-credential-validation" as fullPath
WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts
MERGE (:LocationURI {id: "/" + parts[1]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4]})
WITH parts
MATCH (p1:LocationURI {id: "/" + parts[1]}), (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (p1)-[:PARENT_OF]->(p2)
WITH parts
MATCH (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]}), (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (p2)-[:PARENT_OF]->(p3)
WITH parts
MATCH (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]}), (p4:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4]})
MERGE (p3)-[:PARENT_OF]->(p4);

// 8階層: /config/db/connection/pool/settings/timeout/retry/backoff
WITH "/config/db/connection/pool/settings/timeout/retry/backoff" as fullPath
WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts
MERGE (:LocationURI {id: "/" + parts[1]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7] + "/" + parts[8]})
WITH parts
MATCH (p1:LocationURI {id: "/" + parts[1]}), (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (p1)-[:PARENT_OF]->(p2)
WITH parts
MATCH (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]}), (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (p2)-[:PARENT_OF]->(p3)
WITH parts
MATCH (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]}), (p4:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4]})
MERGE (p3)-[:PARENT_OF]->(p4)
WITH parts
MATCH (p4:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4]}), (p5:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5]})
MERGE (p4)-[:PARENT_OF]->(p5)
WITH parts
MATCH (p5:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5]}), (p6:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6]})
MERGE (p5)-[:PARENT_OF]->(p6)
WITH parts
MATCH (p6:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6]}), (p7:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7]})
MERGE (p6)-[:PARENT_OF]->(p7)
WITH parts
MATCH (p7:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7]}), (p8:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7] + "/" + parts[8]})
MERGE (p7)-[:PARENT_OF]->(p8);