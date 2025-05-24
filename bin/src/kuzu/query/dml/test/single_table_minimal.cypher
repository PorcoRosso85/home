// 1テーブル多粒度モデル（LocationURIのみで完結）
CREATE NODE TABLE LocationURI(id STRING, PRIMARY KEY (id));
CREATE REL TABLE PARENT_OF(FROM LocationURI TO LocationURI);

// 単一パスから階層ノード生成
WITH "/srs/functions/authentication/user-credential-validation" as fullPath
WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts

// 各階層パスのLocationURIノードを作成
MERGE (:LocationURI {id: "/" + parts[1]})
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2]})  
MERGE (:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (:LocationURI {id: fullPath})

// 親子関係作成
WITH parts, fullPath
MATCH (p1:LocationURI {id: "/" + parts[1]}), (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]})
MERGE (p1)-[:PARENT_OF]->(p2)

WITH parts, fullPath
MATCH (p2:LocationURI {id: "/" + parts[1] + "/" + parts[2]}), (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]})
MERGE (p2)-[:PARENT_OF]->(p3)

WITH parts, fullPath
MATCH (p3:LocationURI {id: "/" + parts[1] + "/" + parts[2] + "/" + parts[3]}), (p4:LocationURI {id: fullPath})
MERGE (p3)-[:PARENT_OF]->(p4);