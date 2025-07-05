-- Test data following DDL schema from requirement/graph/ddl/schema.cypher
-- This file contains DML statements for test data

-- Create LocationURI nodes for testing
CREATE (:LocationURI {id: "file:///home/user/project/src/main.py"});
CREATE (:LocationURI {id: "file:///home/user/project/src/utils.py#L42"});
CREATE (:LocationURI {id: "file:///home/user/project/tests/test_main.py#test_function"});
CREATE (:LocationURI {id: "file:///home/user/project/docs/README.md"});
CREATE (:LocationURI {id: "file:///home/user/project/lib/helper.py#HelperClass"});

-- Create RequirementEntity for testing relationships
CREATE (:RequirementEntity {
    id: "req_001",
    title: "User Authentication",
    description: "Implement secure user authentication",
    priority: 128,
    requirement_type: "functional",
    status: "in_progress"
});

CREATE (:RequirementEntity {
    id: "req_002", 
    title: "Data Validation",
    description: "Validate all user inputs",
    priority: 100,
    requirement_type: "functional",
    status: "proposed"
});

-- Create LOCATES relationships
MATCH (l:LocationURI {id: "file:///home/user/project/src/main.py"}),
      (r:RequirementEntity {id: "req_001"})
CREATE (l)-[:LOCATES {entity_type: "requirement", current: true}]->(r);

MATCH (l:LocationURI {id: "file:///home/user/project/src/utils.py#L42"}),
      (r:RequirementEntity {id: "req_002"})
CREATE (l)-[:LOCATES {entity_type: "requirement", current: true}]->(r);