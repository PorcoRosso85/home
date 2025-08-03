"""Debug test to understand the database state."""

import pytest
from .test_e2e_business_scenario import TestE2EBusinessScenario
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class TestDebugBusinessScenario(TestE2EBusinessScenario):
    """Debug version of the business scenario test."""
    
    def test_debug_database_state(self):
        """Debug what's actually in the database."""
        logger.debug("\n=== Debugging Database State ===")
        
        # Check requirements
        reqs = self.graph_adapter.execute_cypher("MATCH (r:RequirementEntity) RETURN r")
        logger.debug(f"\nRequirements: {len(reqs)}")
        
        # Check TestEntity nodes
        test_entities = self.graph_adapter.execute_cypher("MATCH (t:TestEntity) RETURN t")
        logger.debug(f"TestEntity nodes: {len(test_entities)}")
        
        # Check TestSpecification nodes
        test_specs = self.graph_adapter.execute_cypher("MATCH (t:TestSpecification) RETURN t")
        logger.debug(f"TestSpecification nodes: {len(test_specs)}")
        
        # Check relationships
        rels = self.graph_adapter.execute_cypher(
            "MATCH (r:RequirementEntity)-[v:VERIFIED_BY]->(t) RETURN r, type(t) as node_type, count(*) as count"
        )
        logger.debug(f"\nVERIFIED_BY relationships: {len(rels)}")
        for rel in rels:
            logger.debug(f"  {rel}")
        
        # Check specific requirement
        logger.debug("\n=== Checking req_payment_reliability ===")
        
        # Direct query
        direct = self.graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity {id: 'req_payment_reliability'})
            RETURN r
        """)
        logger.debug(f"Direct query found: {len(direct)} nodes")
        
        # Check relationships to any test type
        test_rels = self.graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity {id: 'req_payment_reliability'})-[v:VERIFIED_BY]->(t)
            RETURN labels(t) as labels, t
        """)
        logger.debug(f"Test relationships: {len(test_rels)}")
        for rel in test_rels:
            logger.debug(f"  {rel}")
        
        # Use the adapter method
        tests = self.graph_adapter.get_tests_for_requirement("req_payment_reliability")
        logger.debug(f"\nget_tests_for_requirement returned: {len(tests)} tests")
        for test in tests:
            logger.debug(f"  {test}")