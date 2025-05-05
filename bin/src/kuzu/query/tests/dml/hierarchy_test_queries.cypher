// 階層関係テスト用クエリ

// @name: create_test_location
CREATE (l:LocationURI {
  uri_id: 'hierarchy-test-uri',
  scheme: 'file',
  path: '/src/components/user/profile.ts',
  fragment: 'UserProfile'
})
RETURN l.uri_id, l.path;

// @name: create_parent_location
CREATE (l:LocationURI {
  uri_id: 'hierarchy-parent-uri',
  scheme: 'file',
  path: '/src/components/user'
})
RETURN l.uri_id, l.path;

// @name: create_hierarchy_relationship
MATCH (parent:LocationURI {uri_id: 'hierarchy-parent-uri'}),
      (child:LocationURI {uri_id: 'hierarchy-test-uri'})
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'directory'}]->(child)
RETURN parent.uri_id, child.uri_id;

// @name: get_child_locations
MATCH (parent:LocationURI {uri_id: 'hierarchy-parent-uri'})-[:CONTAINS_LOCATION]->(child:LocationURI)
RETURN parent.path AS parent_path, child.path AS child_path;

// @name: create_test_requirement_with_location
CREATE (r:RequirementEntity {
  id: 'REQ-HIERARCHY-TEST',
  title: '階層テスト要件',
  description: 'これは階層関係テスト用の要件です',
  priority: 'high',
  requirement_type: 'functional'
})
WITH r
MATCH (l:LocationURI {uri_id: 'hierarchy-test-uri'})
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l)
RETURN r.id, l.uri_id;

// @name: create_test_code_with_location
CREATE (c:CodeEntity {
  persistent_id: 'CODE-HIERARCHY-TEST',
  name: 'UserProfileComponent',
  type: 'component',
  signature: 'class UserProfileComponent',
  complexity: 5,
  start_position: 100,
  end_position: 500
})
WITH c
MATCH (l:LocationURI {uri_id: 'hierarchy-test-uri'})
CREATE (c)-[:HAS_LOCATION]->(l)
RETURN c.persistent_id, l.uri_id;

// @name: find_requirements_code_same_location
MATCH (r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)<-[:HAS_LOCATION]-(c:CodeEntity)
RETURN r.id AS requirement_id, r.title AS requirement_title, 
       l.uri_id AS location_uri, l.path AS location_path,
       c.persistent_id AS code_id, c.name AS code_name;

// @name: navigate_hierarchy_structure
MATCH (parent:LocationURI)-[:CONTAINS_LOCATION*]->(child:LocationURI)
OPTIONAL MATCH (r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(child)
OPTIONAL MATCH (c:CodeEntity)-[:HAS_LOCATION]->(child)
RETURN parent.path AS parent_directory,
       child.path AS file_path,
       collect(DISTINCT r.title) AS requirements,
       collect(DISTINCT c.name) AS code_entities;