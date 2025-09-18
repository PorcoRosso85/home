MATCH path = (v1:VersionState)-[:FOLLOWS*]->(v2:VersionState)
WHERE NOT (()-[:FOLLOWS]->(v1))
RETURN [node in nodes(path) | node.id + ": " + node.description] as version_history;