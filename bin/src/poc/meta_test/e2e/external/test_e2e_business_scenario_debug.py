"""Debug test to understand the database state."""

import pytest
from .test_e2e_business_scenario import TestE2EBusinessScenario


class TestDebugBusinessScenario(TestE2EBusinessScenario):
    """Debug version of the business scenario test."""
    
    def test_debug_database_state(self):
        """Debug what's actually in the database."""
        print("\n=== Debugging Database State ===")
        
        # Check requirements
        reqs = self.graph_adapter.execute_cypher("MATCH (r:RequirementEntity) RETURN r")
        print(f"\nRequirements: {len(reqs)}")
        
        # Check TestEntity nodes
        test_entities = self.graph_adapter.execute_cypher("MATCH (t:TestEntity) RETURN t")
        print(f"TestEntity nodes: {len(test_entities)}")
        
        # Check TestSpecification nodes
        test_specs = self.graph_adapter.execute_cypher("MATCH (t:TestSpecification) RETURN t")
        print(f"TestSpecification nodes: {len(test_specs)}")
        
        # Check relationships
        rels = self.graph_adapter.execute_cypher(
            "MATCH (r:RequirementEntity)-[v:VERIFIED_BY]->(t) RETURN r, type(t) as node_type, count(*) as count"
        )
        print(f"\nVERIFIED_BY relationships: {len(rels)}")
        for rel in rels:
            print(f"  {rel}")
        
        # Check specific requirement
        print("\n=== Checking req_payment_reliability ===")
        
        # Direct query
        direct = self.graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity {id: 'req_payment_reliability'})
            RETURN r
        """)
        print(f"Direct query found: {len(direct)} nodes")
        
        # Check relationships to any test type
        test_rels = self.graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity {id: 'req_payment_reliability'})-[v:VERIFIED_BY]->(t)
            RETURN labels(t) as labels, t
        """)
        print(f"Test relationships: {len(test_rels)}")
        for rel in test_rels:
            print(f"  {rel}")
        
        # Use the adapter method
        tests = self.graph_adapter.get_tests_for_requirement("req_payment_reliability")
        print(f"\nget_tests_for_requirement returned: {len(tests)} tests")
        for test in tests:
            print(f"  {test}")