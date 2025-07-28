"""
Integration tests for the complete enforced reference workflow system

This test suite validates the end-to-end functionality of:
1. Enforced workflow with mandatory reference selection
2. Exception handling with approval process
3. Audit trail tracking
4. Completeness reporting
5. Project-wide enforcement
"""
import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from enforced_workflow import EnforcedRequirementWorkflow
from test_completeness_report import TestCompletenessAnalyzer
from reference_repository import create_reference_repository
from asvs_loader import ASVSLoader


class TestEnforcedIntegration:
    """Integration tests for the complete enforced reference system"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def setup_system(self, temp_db):
        """Set up complete system with references and workflow"""
        # Create repository
        repo = create_reference_repository(temp_db)
        # Check if it's an error
        if isinstance(repo, dict) and repo.get("type") in ["DatabaseError", "ValidationError", "NotFoundError"]:
            pytest.fail(f"Failed to create repository: {repo['message']}")
        
        # Load ASVS references using ASVSLoader
        loader = ASVSLoader()
        try:
            # Load sample ASVS data
            cypher_query = loader.load_and_generate("asvs_sample.yaml")
            # Execute the cypher query to load references
            conn = repo["connection"]
            conn.execute(cypher_query)
        except Exception as e:
            print(f"Warning: Could not load ASVS data: {e}")
            # Continue with test - we can still test the workflow
        
        # Create enforced workflow
        workflow = EnforcedRequirementWorkflow(repo, config_path=None)
        
        # Create completeness analyzer
        conn = repo["connection"]  # Use the connection from the repo
        analyzer = TestCompletenessAnalyzer(conn)
        
        return {
            "repo": repo,
            "workflow": workflow,
            "analyzer": analyzer,
            "db_path": temp_db
        }
    
    def test_complete_workflow_with_reference_selection(self, setup_system):
        """Test creating requirements with proper reference selection"""
        workflow = setup_system["workflow"]
        analyzer = setup_system["analyzer"]
        
        # Create authentication requirement with references
        auth_req = {
            "uri": "req://auth/password-policy",
            "title": "Password Policy Implementation",
            "description": "Implement secure password policies",
            "entity_type": "requirement",
            "metadata": {
                "category": "authentication",
                "project": "webapp"
            }
        }
        
        # Select appropriate ASVS references
        selected_refs = [
            "asvs-v4.0.3-2.1.1",  # Password length
            "asvs-v4.0.3-2.1.2",  # Password complexity
            "asvs-v4.0.3-2.1.3"   # Password truncation
        ]
        
        # Create requirement with references
        result = workflow.create_requirement(auth_req, selected_refs)
        assert result["type"] == "Success"
        req_id = result["value"]["requirement_id"]
        
        # Verify requirement was created
        assert req_id == "req://auth/password-policy"
        
        # Verify references were linked
        assert len(result["value"]["references"]) == 3
        
        # Analyze completeness after creation
        coverage = analyzer.analyze_project_coverage()
        assert coverage["overall"]["implemented_requirements"] >= 3
        
        # Check category completeness
        category_analysis = analyzer.analyze_category_completeness()
        auth_coverage = category_analysis.get("authentication", {})
        assert auth_coverage["implemented_count"] >= 3
    
    def test_exception_workflow_integration(self, setup_system):
        """Test exception workflow with approval process"""
        workflow = setup_system["workflow"]
        analyzer = setup_system["analyzer"]
        
        # Create a legacy system requirement with exception
        legacy_req = {
            "uri": "req://legacy/auth-system",
            "title": "Legacy Authentication System",
            "description": "Maintain existing authentication for legacy apps",
            "entity_type": "requirement",
            "metadata": {
                "category": "authentication",
                "project": "legacy-app",
                "system_type": "legacy"
            }
        }
        
        exception_data = {
            "reason": "legacy_system",
            "justification": "System scheduled for retirement in Q3 2024",
            "approver": "security-team",
            "risk_accepted": True,
            "mitigation": "WAF rules and monitoring in place"
        }
        
        # Create with exception
        result = workflow.create_requirement(
            legacy_req,
            selected_references=None,
            exception_data=exception_data
        )
        assert result["type"] == "PendingApproval"
        
        # Approve exception
        approval_result = workflow.approve_exception(
            result["value"]["exception_id"],
            "security-team",
            "Risk accepted with mitigations"
        )
        assert approval_result["type"] == "Success"
        
        # Verify requirement was created
        req_result = workflow.repo["find"](legacy_req["uri"])
        assert req_result["type"] == "Success"
        
        # Check audit trail
        audit_entries = workflow.get_audit_trail("req://legacy/auth-system")
        assert len(audit_entries) >= 2  # Creation and approval
        assert any(e["action"] == "exception_requested" for e in audit_entries)
        assert any(e["action"] == "exception_approved" for e in audit_entries)
    
    def test_project_wide_enforcement(self, setup_system):
        """Test enforcement across multiple projects"""
        workflow = setup_system["workflow"]
        analyzer = setup_system["analyzer"]
        
        projects = ["webapp", "api", "mobile"]
        requirements_created = []
        
        for project in projects:
            # Create requirements for each project
            req_data = {
                "uri": f"req://{project}/session-management",
                "title": f"{project.title()} Session Management",
                "description": f"Session management for {project}",
                "entity_type": "requirement",
                "metadata": {
                    "category": "session",
                    "project": project
                }
            }
            
            # Select session management references
            refs = [
                "asvs-v4.0.3-3.2.1",  # Session token generation
                "asvs-v4.0.3-3.2.2"   # Session token entropy
            ]
            
            result = workflow.create_requirement(req_data, refs)
            assert result["type"] == "Success"
            requirements_created.append(result["value"]["requirement_id"])
        
        # Analyze coverage by project
        coverage = analyzer.analyze_project_coverage()
        
        # Each project should have contributed to coverage
        assert coverage["overall"]["implemented_requirements"] >= 6  # 3 projects × 2 refs
        
        # Generate gap report
        gaps = analyzer.identify_gaps_with_priority()
        
        # High priority gaps should be identified
        high_priority_gaps = [g for g in gaps if g["priority_score"] > 70]
        assert len(high_priority_gaps) > 0
    
    def test_completeness_report_integration(self, setup_system):
        """Test completeness reporting with enforced workflow"""
        workflow = setup_system["workflow"]
        analyzer = setup_system["analyzer"]
        
        # Create a set of requirements covering different categories
        test_requirements = [
            {
                "data": {
                    "uri": "req://crypto/key-management",
                    "title": "Cryptographic Key Management",
                    "description": "Secure key management implementation",
                    "entity_type": "requirement",
                    "metadata": {"category": "cryptography", "project": "core"}
                },
                "refs": ["asvs-v4.0.3-6.2.1", "asvs-v4.0.3-6.2.2"]
            },
            {
                "data": {
                    "uri": "req://access/rbac",
                    "title": "Role-Based Access Control",
                    "description": "RBAC implementation",
                    "entity_type": "requirement",
                    "metadata": {"category": "access_control", "project": "core"}
                },
                "refs": ["asvs-v4.0.3-4.1.3", "asvs-v4.0.3-4.1.4"]
            }
        ]
        
        # Create requirements
        for req_info in test_requirements:
            result = workflow.create_requirement(
                req_info["data"],
                req_info["refs"]
            )
            assert result["type"] == "Success"
        
        # Generate completeness report
        report = analyzer._generate_complete_report()
        
        # Verify report structure
        assert "category_analysis" in report
        assert "project_coverage" in report
        assert "gap_analysis" in report
        assert "summary" in report
        
        # Check category coverage improved
        crypto_coverage = report["category_analysis"].get("cryptography", {})
        assert crypto_coverage["implemented_count"] >= 2
        
        access_coverage = report["category_analysis"].get("access_control", {})
        assert access_coverage["implemented_count"] >= 2
        
        # Verify recommendations are generated
        assert len(report["summary"]["recommendations"]) > 0
    
    def test_audit_trail_completeness(self, setup_system):
        """Test complete audit trail across all operations"""
        workflow = setup_system["workflow"]
        
        # Create requirement with references
        req1 = {
            "uri": "req://audit/test1",
            "title": "Audit Test 1",
            "description": "Test requirement for audit",
            "entity_type": "requirement",
            "metadata": {"category": "authentication", "project": "test"}
        }
        
        result1 = workflow.create_requirement(req1, ["asvs-v4.0.3-2.1.1"])
        assert result1["type"] == "Success"
        
        # Create with exception
        req2 = {
            "uri": "req://audit/test2",
            "title": "Audit Test 2",
            "description": "Test requirement with exception",
            "entity_type": "requirement",
            "metadata": {"category": "session", "project": "test"}
        }
        
        exception = {
            "reason": "poc_system",
            "justification": "POC only",
            "approver": "test-team"
        }
        
        result2 = workflow.create_requirement(req2, None, exception)
        assert result2["type"] == "PendingApproval"
        
        # Approve exception
        workflow.approve_exception(
            result2["value"]["exception_id"],
            "test-team",
            "Approved for POC"
        )
        
        # Get combined audit trail
        all_audit = workflow.audit_logger.get_all_entries()
        
        # Should have entries for both requirements
        req1_audit = [e for e in all_audit if e.get("requirement_id") == "req://audit/test1"]
        req2_audit = [e for e in all_audit if e.get("requirement_id") == "req://audit/test2"]
        
        assert len(req1_audit) >= 1
        assert len(req2_audit) >= 2  # Request and approval
        
        # Verify audit entry structure
        for entry in all_audit:
            assert "timestamp" in entry
            assert "action" in entry
            assert "user" in entry or "approver" in entry
    
    def test_workflow_with_configuration_override(self, setup_system):
        """Test workflow with custom configuration"""
        repo = setup_system["repo"]
        
        # Create custom config
        custom_config = {
            "mandatory_references": {
                "authentication": {
                    "categories": ["passwords", "mfa"],
                    "min_references": 1,
                    "level_requirements": {
                        "1": ["asvs-v4.0.3-2.1.1"]
                    }
                }
            },
            "exception_rules": {
                "allowed_reasons": ["test_only"],
                "require_mitigation": False,
                "approval_required": False
            },
            "enforcement": {
                "strict_mode": False,
                "allow_empty_references": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            config_path = f.name
        
        try:
            # Create workflow with custom config
            custom_workflow = EnforcedRequirementWorkflow(repo, config_path)
            
            # Should allow creation without references due to config
            req = {
                "uri": "req://test/custom-config",
                "title": "Custom Config Test",
                "description": "Testing custom configuration",
                "entity_type": "requirement",
                "metadata": {"category": "other", "project": "test"}
            }
            
            result = custom_workflow.create_requirement(req, [])
            assert result["type"] == "Success"  # Allowed by custom config
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_performance_with_large_dataset(self, setup_system):
        """Test system performance with many requirements"""
        workflow = setup_system["workflow"]
        analyzer = setup_system["analyzer"]
        
        # Create 50 requirements across different categories
        categories = ["authentication", "session", "access_control", "cryptography", "validation"]
        projects = ["app1", "app2", "app3"]
        
        start_time = datetime.now()
        created_count = 0
        
        for i in range(50):
            category = categories[i % len(categories)]
            project = projects[i % len(projects)]
            
            req = {
                "uri": f"req://perf-test/{category}/{i}",
                "title": f"Performance Test {i}",
                "description": f"Requirement {i} for {category}",
                "entity_type": "requirement",
                "metadata": {
                    "category": category,
                    "project": project
                }
            }
            
            # Select 1-3 references based on category
            if category == "authentication":
                refs = ["asvs-v4.0.3-2.1.1"]
            elif category == "session":
                refs = ["asvs-v4.0.3-3.2.1", "asvs-v4.0.3-3.2.2"]
            else:
                refs = ["asvs-v4.0.3-1.1.1"]  # Generic reference
            
            result = workflow.create_requirement(req, refs)
            if result["type"] == "Success":
                created_count += 1
        
        creation_time = (datetime.now() - start_time).total_seconds()
        
        # Should create all requirements reasonably fast
        assert created_count == 50
        assert creation_time < 10  # Should complete in under 10 seconds
        
        # Test analysis performance
        analysis_start = datetime.now()
        
        category_analysis = analyzer.analyze_category_completeness()
        project_coverage = analyzer.analyze_project_coverage()
        gaps = analyzer.identify_gaps_with_priority()
        
        analysis_time = (datetime.now() - analysis_start).total_seconds()
        
        # Analysis should also be fast
        assert analysis_time < 5  # Should complete in under 5 seconds
        
        # Verify results are meaningful
        assert len(category_analysis) >= 5
        assert project_coverage["overall"]["total_requirements"] > 0
        assert len(gaps) > 0


def test_integration_scenarios():
    """Test various integration scenarios"""
    print("Testing Enforced Reference Integration...")
    
    # Run pytest on this file
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    test_integration_scenarios()