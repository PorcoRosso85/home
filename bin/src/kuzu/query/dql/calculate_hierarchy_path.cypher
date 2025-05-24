// 階層パス計算クエリ
// 指定されたリーフノードからルートまでのフルパスを構築

MATCH (root:Level1)-[:CONTAINS]->(l2:Level2)-[:CONTAINS]->(l3:Level3)-[:CONTAINS]->(leaf:Level4 {name: $leafName})
RETURN concat("/", root.name, "/", l2.name, "/", l3.name, "/", leaf.name, "/") as full_path;