"""
Test Enforced Workflow - Executable Specification

This test file serves as an executable specification for the business rules
around enforced reference association in the requirement management system.

Business Rules:
1. Cannot create requirement without reference selection or exception
2. Must provide justification for exceptions
3. Workflow states are tracked
4. All operations are auditable
"""
import pytest
from typing import Dict, Any, Optional, List
from datetime import datetime


class TestEnforcedReferenceWorkflow:
    """Specification for enforced reference association workflow"""
    
    def test_requirement_creation_requires_reference_or_exception(self, workflow_repo):
        """SPEC: A requirement cannot be created without either selecting a reference or providing an exception"""
        # Given: A new requirement without reference
        requirement = {
            "id": "REQ-001",
            "title": "User Authentication",
            "description": "Users must authenticate before accessing the system"
        }
        
        # When: Attempting to create without reference or exception
        result = workflow_repo["create_requirement"](requirement)
        
        # Then: Creation should fail with clear error
        assert result["type"] == "ValidationError"
        assert "reference" in result["message"].lower()
        assert result["code"] == "REFERENCE_REQUIRED"
        assert result["suggestion"] == "Either select relevant references or provide exception justification"
    
    def test_requirement_creation_with_reference_succeeds(self, workflow_repo):
        """SPEC: A requirement can be created when associated with one or more references"""
        # Given: A requirement with reference associations
        requirement = {
            "id": "REQ-001",
            "title": "Password Minimum Length",
            "description": "Passwords must be at least 12 characters",
            "references": ["ASVS_V2.1.1", "NIST_800-63B_5.1.1"]
        }
        
        # When: Creating the requirement
        result = workflow_repo["create_requirement"](requirement)
        
        # Then: Creation succeeds and references are linked
        assert result["type"] == "Success"
        assert result["requirement"]["id"] == "REQ-001"
        assert result["requirement"]["workflow_state"] == "draft"
        assert len(result["linked_references"]) == 2
        assert all(ref["status"] == "planned" for ref in result["linked_references"])
    
    def test_exception_requires_justification(self, workflow_repo):
        """SPEC: Creating a requirement without references requires exception justification"""
        # Given: A requirement with insufficient exception justification
        requirement = {
            "id": "REQ-002",
            "title": "Custom Security Feature",
            "description": "Proprietary security mechanism",
            "exception": {
                "reason": "custom"  # Too brief
            }
        }
        
        # When: Attempting to create with insufficient justification
        result = workflow_repo["create_requirement"](requirement)
        
        # Then: Should fail requiring detailed justification
        assert result["type"] == "ValidationError"
        assert "justification" in result["message"].lower()
        assert result["minimum_justification_length"] == 50
        assert result["valid_exception_types"] == [
            "not_applicable",
            "compensating_control", 
            "risk_accepted",
            "custom_implementation"
        ]
    
    def test_valid_exception_allows_creation(self, workflow_repo):
        """SPEC: A properly justified exception allows requirement creation without references"""
        # Given: A requirement with valid exception
        requirement = {
            "id": "REQ-003",
            "title": "Internal Audit Log",
            "description": "Log all administrative actions",
            "exception": {
                "type": "custom_implementation",
                "justification": "This is an internal compliance requirement specific to our industry regulations that is not covered by standard security frameworks",
                "approved_by": "security_architect",
                "review_date": "2024-01-15"
            }
        }
        
        # When: Creating with valid exception
        result = workflow_repo["create_requirement"](requirement)
        
        # Then: Creation succeeds with exception tracked
        assert result["type"] == "Success"
        assert result["requirement"]["has_exception"] is True
        assert result["requirement"]["workflow_state"] == "draft"
        assert result["exception_record"]["type"] == "custom_implementation"
        assert result["exception_record"]["requires_periodic_review"] is True
    
    def test_workflow_state_transitions(self, workflow_repo):
        """SPEC: Requirements follow defined workflow states with proper transitions"""
        # Given: A requirement in draft state
        requirement_id = "REQ-004"
        
        # Create requirement
        create_result = workflow_repo["create_requirement"]({
            "id": requirement_id,
            "title": "Session Management",
            "description": "Secure session handling",
            "references": ["ASVS_V3.2.1"]
        })
        assert create_result["requirement"]["workflow_state"] == "draft"
        
        # When: Moving through workflow states
        # Draft -> Under Review
        review_result = workflow_repo["transition_workflow"](
            requirement_id, 
            "submit_for_review",
            {"reviewer": "lead_architect"}
        )
        assert review_result["type"] == "Success"
        assert review_result["new_state"] == "under_review"
        assert review_result["timestamp"] is not None
        
        # Under Review -> Approved
        approve_result = workflow_repo["transition_workflow"](
            requirement_id,
            "approve",
            {"approver": "security_team", "comments": "Meets security standards"}
        )
        assert approve_result["type"] == "Success" 
        assert approve_result["new_state"] == "approved"
        
        # Then: Invalid transitions should fail
        invalid_result = workflow_repo["transition_workflow"](
            requirement_id,
            "submit_for_review",  # Can't go back to review from approved
            {}
        )
        assert invalid_result["type"] == "InvalidTransitionError"
        assert invalid_result["current_state"] == "approved"
        assert invalid_result["valid_transitions"] == ["implement", "deprecate"]
    
    def test_reference_coverage_tracking(self, workflow_repo):
        """SPEC: System tracks which references are covered by requirements"""
        # Given: Multiple requirements covering different references
        requirements = [
            {
                "id": "REQ-PWD-001",
                "title": "Password Length",
                "references": ["ASVS_V2.1.1"]
            },
            {
                "id": "REQ-PWD-002", 
                "title": "Password Complexity",
                "references": ["ASVS_V2.1.4", "ASVS_V2.1.5"]
            }
        ]
        
        for req in requirements:
            workflow_repo["create_requirement"](req)
        
        # When: Checking coverage
        coverage = workflow_repo["get_reference_coverage"]("ASVS", "authentication")
        
        # Then: Should show accurate coverage metrics
        assert coverage["type"] == "Success"
        assert coverage["statistics"]["total_references"] == 10  # Total ASVS auth references
        assert coverage["statistics"]["covered_references"] == 3
        assert coverage["statistics"]["coverage_percentage"] == 30.0
        assert "ASVS_V2.1.1" in coverage["covered_references"]
        assert "ASVS_V2.1.2" in coverage["uncovered_references"]
    
    def test_audit_trail_for_all_operations(self, workflow_repo):
        """SPEC: All operations must be auditable with complete history"""
        # Given: A requirement with various operations
        requirement_id = "REQ-AUDIT-001"
        
        # Create
        workflow_repo["create_requirement"]({
            "id": requirement_id,
            "title": "Initial Title",
            "references": ["ASVS_V4.1.1"]
        })
        
        # Update
        workflow_repo["update_requirement"](requirement_id, {
            "title": "Updated Title",
            "description": "Added description"
        })
        
        # Add reference
        workflow_repo["add_reference"](requirement_id, "ASVS_V4.1.2", {
            "reason": "Additional coverage needed"
        })
        
        # Transition workflow
        workflow_repo["transition_workflow"](requirement_id, "submit_for_review", {
            "reviewer": "security_team"
        })
        
        # When: Retrieving audit trail
        audit_trail = workflow_repo["get_audit_trail"](requirement_id)
        
        # Then: Complete history should be available
        assert audit_trail["type"] == "Success"
        assert len(audit_trail["events"]) == 4
        
        # Verify each event has required audit fields
        for event in audit_trail["events"]:
            assert event["timestamp"] is not None
            assert event["actor"] is not None
            assert event["action"] in [
                "requirement_created",
                "requirement_updated", 
                "reference_added",
                "workflow_transitioned"
            ]
            assert event["details"] is not None
            
        # Verify chronological order
        timestamps = [event["timestamp"] for event in audit_trail["events"]]
        assert timestamps == sorted(timestamps)
    
    def test_bulk_reference_suggestion(self, workflow_repo):
        """SPEC: System can suggest relevant references based on requirement content"""
        # Given: A requirement without references
        requirement = {
            "id": "REQ-005",
            "title": "Multi-factor Authentication",
            "description": "Users must provide two factors for authentication including something they know and something they have"
        }
        
        # When: Requesting reference suggestions
        suggestions = workflow_repo["suggest_references"](requirement)
        
        # Then: Should receive relevant suggestions
        assert suggestions["type"] == "Success"
        assert len(suggestions["suggestions"]) > 0
        
        # Verify suggestions are relevant (contain MFA-related references)
        suggested_ids = [s["reference_id"] for s in suggestions["suggestions"]]
        assert any("V2.4" in ref_id for ref_id in suggested_ids)  # ASVS MFA section
        
        # Each suggestion should have relevance score and reason
        for suggestion in suggestions["suggestions"]:
            assert 0 <= suggestion["relevance_score"] <= 1.0
            assert suggestion["match_reason"] is not None
            assert suggestion["reference_details"] is not None
    
    def test_periodic_review_enforcement(self, workflow_repo):
        """SPEC: Requirements with exceptions must undergo periodic review"""
        # Given: A requirement created with exception 90 days ago
        old_requirement = {
            "id": "REQ-OLD-001",
            "title": "Legacy Integration",
            "exception": {
                "type": "compensating_control",
                "justification": "Using proprietary encryption due to legacy system constraints",
                "review_period_days": 90
            },
            "created_date": "2023-10-01"  # More than 90 days ago
        }
        
        workflow_repo["create_requirement"](old_requirement)
        
        # When: Checking for required reviews
        pending_reviews = workflow_repo["get_pending_exception_reviews"]()
        
        # Then: Should identify requirement needing review
        assert pending_reviews["type"] == "Success"
        assert len(pending_reviews["requirements"]) > 0
        assert "REQ-OLD-001" in [r["id"] for r in pending_reviews["requirements"]]
        
        review_item = next(r for r in pending_reviews["requirements"] if r["id"] == "REQ-OLD-001")
        assert review_item["days_overdue"] > 0
        assert review_item["last_review_date"] == "2023-10-01"
        assert review_item["next_review_date"] == "2023-12-30"
    
    def test_reference_implementation_status_tracking(self, workflow_repo):
        """SPEC: Track implementation status of each reference within a requirement"""
        # Given: A requirement with multiple references
        requirement_id = "REQ-IMPL-001"
        workflow_repo["create_requirement"]({
            "id": requirement_id,
            "title": "Comprehensive Password Policy",
            "references": ["ASVS_V2.1.1", "ASVS_V2.1.2", "ASVS_V2.1.3"]
        })
        
        # When: Updating implementation status of individual references
        # Mark first reference as implemented
        impl_result1 = workflow_repo["update_reference_status"](
            requirement_id,
            "ASVS_V2.1.1",
            {
                "status": "implemented",
                "evidence": "Unit test: test_password_length.py",
                "verified_by": "qa_team",
                "verified_date": "2024-01-20"
            }
        )
        assert impl_result1["type"] == "Success"
        
        # Mark second as partially implemented
        impl_result2 = workflow_repo["update_reference_status"](
            requirement_id,
            "ASVS_V2.1.2",
            {
                "status": "partial",
                "notes": "Supports 64 chars, working on 128",
                "target_date": "2024-02-01"
            }
        )
        assert impl_result2["type"] == "Success"
        
        # Then: Requirement should reflect composite status
        req_status = workflow_repo["get_requirement_status"](requirement_id)
        assert req_status["type"] == "Success"
        assert req_status["overall_implementation"] == "in_progress"
        assert req_status["reference_summary"] == {
            "total": 3,
            "implemented": 1,
            "partial": 1,
            "planned": 1
        }
        assert req_status["completion_percentage"] == 50.0  # (1 + 0.5 + 0) / 3
    
    def test_compliance_report_generation(self, workflow_repo):
        """SPEC: Generate compliance reports showing standard adherence"""
        # Given: Multiple requirements with various implementation states
        test_data = [
            {
                "id": "REQ-COMP-001",
                "title": "Password Policy",
                "references": ["ASVS_V2.1.1"],
                "ref_status": "implemented"
            },
            {
                "id": "REQ-COMP-002", 
                "title": "Account Lockout",
                "references": ["ASVS_V2.2.1"],
                "ref_status": "implemented"
            },
            {
                "id": "REQ-COMP-003",
                "title": "Password Recovery",
                "references": ["ASVS_V2.3.1"],
                "ref_status": "planned"
            }
        ]
        
        for data in test_data:
            req_result = workflow_repo["create_requirement"]({
                "id": data["id"],
                "title": data["title"],
                "references": data["references"]
            })
            if data["ref_status"] != "planned":
                workflow_repo["update_reference_status"](
                    data["id"],
                    data["references"][0],
                    {"status": data["ref_status"]}
                )
        
        # When: Generating compliance report
        report = workflow_repo["generate_compliance_report"]({
            "standard": "ASVS",
            "version": "4.0.3",
            "level": 1,
            "categories": ["authentication"]
        })
        
        # Then: Report should provide comprehensive compliance view
        assert report["type"] == "Success"
        assert report["report"]["standard"] == "ASVS"
        assert report["report"]["generated_date"] is not None
        assert report["report"]["overall_compliance"] == 66.7  # 2 of 3 implemented
        
        # Category breakdown
        auth_category = report["report"]["by_category"]["authentication"]
        assert auth_category["total_controls"] >= 3
        assert auth_category["implemented"] == 2
        assert auth_category["compliance_percentage"] == 66.7
        
        # Gap analysis included
        assert len(report["report"]["gaps"]) == 1
        assert report["report"]["gaps"][0]["reference"] == "ASVS_V2.3.1"
        assert report["report"]["gaps"][0]["requirement"] == "REQ-COMP-003"


@pytest.fixture
def workflow_repo():
    """Create a test repository with workflow enforcement"""
    from poc.uri.enforced_workflow import create_workflow_repository
    import os
    
    # Set environment variable to skip schema check
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "1"
    
    # Create in-memory workflow repository
    return create_workflow_repository(":memory:")


class TestWorkflowBusinessRules:
    """Additional business rule specifications"""
    
    def test_cannot_approve_requirement_with_unresolved_comments(self, workflow_repo):
        """SPEC: Requirements cannot be approved if they have unresolved review comments"""
        # Given: A requirement under review with comments
        requirement_id = "REQ-REVIEW-001"
        workflow_repo["create_requirement"]({
            "id": requirement_id,
            "title": "Data Encryption",
            "references": ["ASVS_V6.1.1"]
        })
        
        workflow_repo["transition_workflow"](requirement_id, "submit_for_review", {})
        
        # Add review comments
        workflow_repo["add_review_comment"](requirement_id, {
            "author": "security_reviewer",
            "comment": "Need to specify encryption algorithm",
            "severity": "must_fix"
        })
        
        # When: Attempting to approve with unresolved comments
        result = workflow_repo["transition_workflow"](requirement_id, "approve", {
            "approver": "lead_architect"
        })
        
        # Then: Should fail
        assert result["type"] == "ValidationError"
        assert result["code"] == "UNRESOLVED_COMMENTS"
        assert result["unresolved_count"] == 1
        assert result["must_fix_count"] == 1
    
    def test_reference_deprecation_handling(self, workflow_repo):
        """SPEC: Handle deprecated references appropriately"""
        # Given: A requirement linked to a reference that becomes deprecated
        requirement_id = "REQ-DEPR-001"
        workflow_repo["create_requirement"]({
            "id": requirement_id,
            "title": "Legacy Auth Check",
            "references": ["ASVS_V2.OLD.1"]  # Will be deprecated
        })
        
        # When: Reference is marked as deprecated
        deprecation_result = workflow_repo["deprecate_reference"]("ASVS_V2.OLD.1", {
            "reason": "Superseded by V2.NEW.1",
            "replacement": "ASVS_V2.NEW.1",
            "deprecation_date": "2024-01-01",
            "sunset_date": "2024-12-31"
        })
        
        # Then: Requirements should be notified
        notifications = workflow_repo["get_deprecation_impacts"]("ASVS_V2.OLD.1")
        assert notifications["type"] == "Success"
        assert requirement_id in notifications["affected_requirements"]
        assert notifications["suggested_action"] == "migrate_reference"
        assert notifications["replacement_reference"] == "ASVS_V2.NEW.1"
    
    def test_requirement_templates_with_references(self, workflow_repo):
        """SPEC: Templates can predefine reference associations"""
        # Given: A template for authentication requirements
        template_result = workflow_repo["create_template"]({
            "id": "TMPL-AUTH-BASIC",
            "name": "Basic Authentication Requirements",
            "description": "Standard set of authentication requirements",
            "preset_references": [
                "ASVS_V2.1.1",  # Password length
                "ASVS_V2.2.1",  # Account lockout
                "ASVS_V2.5.1",  # Credential recovery
            ],
            "requirement_templates": [
                {
                    "title_template": "Password Policy Implementation",
                    "description_template": "Implement password policy meeting ASVS requirements",
                    "reference_mappings": ["ASVS_V2.1.1"]
                }
            ]
        })
        assert template_result["type"] == "Success"
        
        # When: Creating requirements from template
        instance_result = workflow_repo["instantiate_template"]("TMPL-AUTH-BASIC", {
            "project": "WebApp2024",
            "prefix": "WEB"
        })
        
        # Then: Requirements should be created with predefined references
        assert instance_result["type"] == "Success"
        assert len(instance_result["created_requirements"]) > 0
        
        first_req = instance_result["created_requirements"][0]
        assert first_req["id"].startswith("WEB-")
        assert len(first_req["references"]) > 0
        assert "ASVS_V2.1.1" in first_req["references"]