// import_parquet.cypher
// このファイルは他のすべてのDQLファイルを実行するためのメタスクリプトです
// main.tsが特別に探すファイル名なので、他のDQLファイルを呼び出す橋渡し役として機能します

// basic_queries.cypher をインポート
SOURCE "/dql/basic_queries.cypher";

// convention.cypher をインポート
SOURCE "/dql/convention.cypher";

// coverage_measurement_queries.cypher をインポート
SOURCE "/dql/coverage_measurement_queries.cypher";

// dependency_analysis_queries.cypher をインポート
SOURCE "/dql/dependency_analysis_queries.cypher";

// exclusive_relation_queries.cypher をインポート
SOURCE "/dql/exclusive_relation_queries.cypher";

// export_parquet.cypher は飛ばします
// このファイルはデータをエクスポートするためのものなので、初期ロード時には実行しません

// external_reference_queries.cypher をインポート
SOURCE "/dql/external_reference_queries.cypher";

// implementation_traceability_queries.cypher をインポート
SOURCE "/dql/implementation_traceability_queries.cypher";

// living_documentation_queries.cypher をインポート
SOURCE "/dql/living_documentation_queries.cypher";

// location_hierarchy_queries.cypher をインポート
SOURCE "/dql/location_hierarchy_queries.cypher";

// result_binding_queries.cypher をインポート
SOURCE "/dql/result_binding_queries.cypher";

// version_queries.cypher をインポート
SOURCE "/dql/version_queries.cypher";

// version_state_restore_queries.cypher をインポート
SOURCE "/dql/version_state_restore_queries.cypher";

// すべてのDQLファイルを実行しました
MATCH (n) RETURN count(n) as total_node_count;
