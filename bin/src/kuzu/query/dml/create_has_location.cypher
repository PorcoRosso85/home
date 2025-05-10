// HAS_LOCATIONエッジを作成するクエリ
MATCH (from:CodeEntity {id: $from_id})
MATCH (to:LocationURI {id: $to_id})
CREATE (from)-[has_location:HAS_LOCATION {}]->(to)
RETURN has_location
