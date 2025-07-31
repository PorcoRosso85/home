"""Helper functions for E2E tests."""

from typing import Any

from ...infrastructure.graph_adapter import GraphAdapter
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


def ensure_test_compatibility(graph_adapter: GraphAdapter) -> None:
    """Ensure compatibility between TestEntity and TestSpecification nodes.
    
    The DDL creates TestEntity nodes but GraphAdapter expects TestSpecification.
    This function creates corresponding TestSpecification nodes.
    
    Args:
        graph_adapter: The graph adapter instance
    """
    try:
        # Find all TestEntity nodes
        test_entities = graph_adapter.execute_cypher("""
            MATCH (t:TestEntity)
            RETURN t.id as id, t.test_type as test_type, t.name as name, t.description as description
        """)
        
        logger.debug(f"Found {len(test_entities)} TestEntity nodes to migrate")
        
        # Create corresponding TestSpecification nodes
        for test in test_entities:
            # Extract values - handle the simplified column mapping
            test_id = test.get("col0") or test.get("id")
            test_type = test.get("col1") or test.get("test_type", "unit")
            name = test.get("col2") or test.get("name", "")
            description = test.get("col3") or test.get("description", "")
            
            logger.debug(f"Processing TestEntity: id={test_id}, type={test_type}, raw={test}")
            
            if test_id:
                graph_adapter.execute_cypher("""
                    MERGE (t:TestSpecification {id: $id})
                    SET t.test_type = $test_type,
                        t.name = $name,
                        t.description = $description
                """, {
                    "id": test_id,
                    "test_type": test_type,
                    "name": name,
                    "description": description
                })
                
        # Copy VERIFIED_BY relationships
        relationships = graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity)-[v:VERIFIED_BY]->(t:TestEntity)
            RETURN r.id as req_id, t.id as test_id, v.verification_type as v_type, v.coverage_score as score
        """)
        
        logger.debug(f"Found {len(relationships)} VERIFIED_BY relationships to migrate")
        
        for rel in relationships:
            # Extract values
            req_id = rel.get("col0") or rel.get("req_id")
            test_id = rel.get("col1") or rel.get("test_id")
            v_type = rel.get("col2") or rel.get("v_type", "behavior")
            score = rel.get("col3") or rel.get("score", 0.0)
            
            logger.debug(f"Processing relationship: req={req_id}, test={test_id}, type={v_type}, score={score}, raw={rel}")
            
            if req_id and test_id:
                graph_adapter.execute_cypher("""
                    MATCH (r:RequirementEntity {id: $req_id})
                    MATCH (t:TestSpecification {id: $test_id})
                    MERGE (r)-[v:VERIFIED_BY]->(t)
                    SET v.verification_type = $v_type,
                        v.coverage_score = $score
                """, {
                    "req_id": req_id,
                    "test_id": test_id,
                    "v_type": v_type,
                    "score": score
                })
                
        logger.info("Test compatibility ensured between TestEntity and TestSpecification")
        
    except Exception as e:
        logger.error(f"Error ensuring test compatibility: {e}")
        # Don't fail - continue with what we have


def create_test_execution_nodes(graph_adapter: GraphAdapter, 
                                test_id: str,
                                execution_data: dict[str, Any]) -> None:
    """Create TestExecution nodes in the graph.
    
    Args:
        graph_adapter: The graph adapter instance
        test_id: The test ID
        execution_data: Execution data including timestamp, passed, duration_ms
    """
    try:
        exec_id = f"exec_{test_id}_{execution_data.get('timestamp', 'unknown')}"
        
        graph_adapter.execute_cypher("""
            CREATE (e:TestExecution {
                id: $id,
                test_id: $test_id,
                timestamp: $timestamp,
                passed: $passed,
                duration_ms: $duration_ms,
                error_message: $error_message
            })
        """, {
            "id": exec_id,
            "test_id": test_id,
            "timestamp": execution_data.get("timestamp", ""),
            "passed": execution_data.get("passed", True),
            "duration_ms": execution_data.get("duration_ms", 0),
            "error_message": execution_data.get("error_message", "")
        })
        
    except Exception as e:
        logger.error(f"Error creating test execution node: {e}")