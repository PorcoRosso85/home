// HAS_LOCATIONエッジを作成するクエリ
MATCH (from:CodeEntity {persistent_id: $from_id})
MATCH (to:LocationURI {uri_id: $to_id})
CREATE (from)-[has_location:HAS_LOCATION {}]->(to)
RETURN has_location
