"""
Test Exception Workflow - Comprehensive Specification

This test file specifies the complete exception workflow for requirements that cannot
follow standard reference associations. It covers:

1. Exception request creation with required fields
2. Multi-level approval workflow
3. Complete audit trail for exception lifecycle
4. Periodic review reminders and enforcement
5. Exception metrics and reporting

Business Rules:
- Exceptions must have detailed justification (minimum 50 characters)
- Exceptions require approval from designated roles
- All exceptions must be periodically reviewed (default: 90 days)
- Exception history is immutable and auditable
- Metrics track exception usage patterns
"""
import pytest
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class ExceptionType(Enum):
    """Valid exception types"""
    NOT_APPLICABLE = "not_applicable"
    COMPENSATING_CONTROL = "compensating_control"
    RISK_ACCEPTED = "risk_accepted"
    CUSTOM_IMPLEMENTATION = "custom_implementation"
    LEGACY_SYSTEM = "legacy_system"
    TEMPORARY_WAIVER = "temporary_waiver"


class ApprovalLevel(Enum):
    """Approval levels for exceptions"""
    TEAM_LEAD = "team_lead"
    SECURITY_ARCHITECT = "security_architect"
    RISK_MANAGEMENT = "risk_management"
    EXECUTIVE = "executive"


class ExceptionStatus(Enum):
    """Exception request status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TestExceptionRequestCreation:
    """Specification for exception request creation"""
    
    def test_exception_request_requires_all_fields(self, workflow_repo):
        """SPEC: Exception request must include all required fields"""
        # Given: An incomplete exception request
        exception_request = {
            "requirement_id": "REQ-001",
            "type": ExceptionType.RISK_ACCEPTED.value,
            # Missing justification and other required fields
        }
        
        # When: Attempting to create exception
        result = workflow_repo["create_exception_request"](exception_request)
        
        # Then: Should fail with validation error
        assert result["type"] == "ValidationError"
        assert result["code"] == "MISSING_REQUIRED_FIELDS"
        assert "justification" in result["missing_fields"]
        assert "risk_assessment" in result["missing_fields"]
        assert "compensating_controls" in result["missing_fields"]
    
    def test_exception_justification_minimum_length(self, workflow_repo):
        """SPEC: Exception justification must be at least 50 characters"""
        # Given: Exception with short justification
        exception_request = {
            "requirement_id": "REQ-001",
            "type": ExceptionType.RISK_ACCEPTED.value,
            "justification": "Too short",
            "risk_assessment": "Low risk system",
            "compensating_controls": ["Manual review process"]
        }
        
        # When: Creating exception request
        result = workflow_repo["create_exception_request"](exception_request)
        
        # Then: Should fail validation
        assert result["type"] == "ValidationError"
        assert result["code"] == "INSUFFICIENT_JUSTIFICATION"
        assert result["minimum_length"] == 50
        assert result["provided_length"] == 9
    
    def test_valid_exception_request_creation(self, workflow_repo):
        """SPEC: Valid exception request creates pending approval record"""
        # Given: Complete exception request
        exception_request = {
            "requirement_id": "REQ-001",
            "type": ExceptionType.COMPENSATING_CONTROL.value,
            "justification": "Legacy authentication system cannot be modified to support modern standards without complete rewrite",
            "risk_assessment": "Medium risk - authentication bypass possible but mitigated by network controls",
            "compensating_controls": [
                "Network isolation of legacy system",
                "Additional monitoring and alerting",
                "Quarterly penetration testing"
            ],
            "business_impact": "Critical - supports 10K daily transactions",
            "expiration_date": (datetime.now() + timedelta(days=180)).isoformat(),
            "requestor": "john.doe@company.com"
        }
        
        # When: Creating exception request
        result = workflow_repo["create_exception_request"](exception_request)
        
        # Then: Should succeed with tracking number
        assert result["type"] == "Success"
        assert result["exception_id"].startswith("EXC-")
        assert result["status"] == ExceptionStatus.PENDING_APPROVAL.value
        assert result["created_at"] is not None
        assert result["approval_required"] == [ApprovalLevel.SECURITY_ARCHITECT.value]
    
    def test_exception_type_determines_approval_requirements(self, workflow_repo):
        """SPEC: Different exception types require different approval levels"""
        test_cases = [
            {
                "type": ExceptionType.NOT_APPLICABLE.value,
                "expected_approvers": [ApprovalLevel.TEAM_LEAD.value]
            },
            {
                "type": ExceptionType.COMPENSATING_CONTROL.value,
                "expected_approvers": [ApprovalLevel.SECURITY_ARCHITECT.value]
            },
            {
                "type": ExceptionType.RISK_ACCEPTED.value,
                "expected_approvers": [
                    ApprovalLevel.SECURITY_ARCHITECT.value,
                    ApprovalLevel.RISK_MANAGEMENT.value
                ]
            },
            {
                "type": ExceptionType.TEMPORARY_WAIVER.value,
                "expected_approvers": [
                    ApprovalLevel.SECURITY_ARCHITECT.value,
                    ApprovalLevel.EXECUTIVE.value
                ]
            }
        ]
        
        for test_case in test_cases:
            # Create exception of specific type
            request = self._create_valid_exception_request()
            request["type"] = test_case["type"]
            
            result = workflow_repo["create_exception_request"](request)
            
            assert result["type"] == "Success"
            assert result["approval_required"] == test_case["expected_approvers"]
    
    def test_temporary_exceptions_require_expiration(self, workflow_repo):
        """SPEC: Temporary exceptions must have expiration date"""
        # Given: Temporary exception without expiration
        request = self._create_valid_exception_request()
        request["type"] = ExceptionType.TEMPORARY_WAIVER.value
        request.pop("expiration_date", None)
        
        # When: Creating temporary exception
        result = workflow_repo["create_exception_request"](request)
        
        # Then: Should fail
        assert result["type"] == "ValidationError"
        assert result["code"] == "EXPIRATION_REQUIRED"
        assert result["message"] == "Temporary exceptions must have expiration date"
    
    def _create_valid_exception_request(self) -> Dict[str, Any]:
        """Helper to create valid exception request"""
        return {
            "requirement_id": "REQ-001",
            "type": ExceptionType.COMPENSATING_CONTROL.value,
            "justification": "System constraints prevent standard implementation - using alternative controls",
            "risk_assessment": "Low to medium risk with compensating controls in place",
            "compensating_controls": ["Control 1", "Control 2"],
            "business_impact": "Medium - affects subset of users",
            "requestor": "user@company.com"
        }


class TestApprovalWorkflow:
    """Specification for multi-level approval workflow"""
    
    def test_sequential_approval_for_multiple_levels(self, workflow_repo):
        """SPEC: Multi-level approvals must be completed in sequence"""
        # Given: Exception requiring multiple approvals
        request = {
            "requirement_id": "REQ-002",
            "type": ExceptionType.RISK_ACCEPTED.value,
            "justification": "Critical business function requires accepting known security risk due to partner constraints",
            "risk_assessment": "High risk - potential data exposure, mitigated by encryption and monitoring",
            "compensating_controls": ["Encryption at rest", "Enhanced monitoring", "Quarterly audits"],
            "business_impact": "Critical - $1M daily revenue impact",
            "requestor": "product.owner@company.com"
        }
        
        # Create exception requiring security architect and risk management approval
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: Attempting to approve out of order (risk management first)
        risk_approval = workflow_repo["approve_exception"](exception_id, {
            "approver": "risk.manager@company.com",
            "role": ApprovalLevel.RISK_MANAGEMENT.value,
            "comments": "Risk acceptable with controls"
        })
        
        # Then: Should fail - must get security architect approval first
        assert risk_approval["type"] == "ValidationError"
        assert risk_approval["code"] == "APPROVAL_SEQUENCE_VIOLATION"
        assert risk_approval["next_required_approver"] == ApprovalLevel.SECURITY_ARCHITECT.value
        
        # When: Approving in correct order
        # First approval - security architect
        sec_approval = workflow_repo["approve_exception"](exception_id, {
            "approver": "security.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Controls adequately mitigate technical risk"
        })
        assert sec_approval["type"] == "Success"
        assert sec_approval["remaining_approvals"] == [ApprovalLevel.RISK_MANAGEMENT.value]
        
        # Second approval - risk management
        risk_approval2 = workflow_repo["approve_exception"](exception_id, {
            "approver": "risk.manager@company.com",
            "role": ApprovalLevel.RISK_MANAGEMENT.value,
            "comments": "Business risk accepted"
        })
        assert risk_approval2["type"] == "Success"
        assert risk_approval2["status"] == ExceptionStatus.APPROVED.value
        assert risk_approval2["remaining_approvals"] == []
    
    def test_rejection_terminates_approval_chain(self, workflow_repo):
        """SPEC: Rejection by any approver terminates the approval process"""
        # Given: Exception pending approval
        request = self._create_risk_exception()
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: First approver rejects
        rejection = workflow_repo["reject_exception"](exception_id, {
            "approver": "security.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "reason": "Insufficient compensating controls for risk level",
            "recommendations": [
                "Add network segmentation",
                "Implement application-level encryption",
                "Increase monitoring frequency"
            ]
        })
        
        # Then: Exception is rejected and cannot be further approved
        assert rejection["type"] == "Success"
        assert rejection["status"] == ExceptionStatus.REJECTED.value
        assert rejection["can_resubmit"] is True
        assert rejection["resubmission_requirements"] == ["Address rejection reasons"]
        
        # Attempting further approval should fail
        attempt_approval = workflow_repo["approve_exception"](exception_id, {
            "approver": "risk.manager@company.com",
            "role": ApprovalLevel.RISK_MANAGEMENT.value,
            "comments": "Trying to approve rejected"
        })
        assert attempt_approval["type"] == "ValidationError"
        assert attempt_approval["code"] == "EXCEPTION_REJECTED"
    
    def test_approval_delegation(self, workflow_repo):
        """SPEC: Approvers can delegate to authorized alternates"""
        # Given: Exception pending approval
        request = self._create_risk_exception()
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: Approver delegates to alternate
        delegation = workflow_repo["delegate_approval"](exception_id, {
            "from_approver": "security.architect@company.com",
            "to_approver": "deputy.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "reason": "Out of office",
            "expiration": (datetime.now() + timedelta(days=7)).isoformat()
        })
        
        # Then: Delegation is recorded
        assert delegation["type"] == "Success"
        assert delegation["delegation_id"] is not None
        
        # And: Delegate can approve
        delegate_approval = workflow_repo["approve_exception"](exception_id, {
            "approver": "deputy.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Approved on behalf of primary approver",
            "delegation_id": delegation["delegation_id"]
        })
        assert delegate_approval["type"] == "Success"
    
    def test_conditional_approval_with_requirements(self, workflow_repo):
        """SPEC: Approvers can grant conditional approval with requirements"""
        # Given: Exception pending approval
        request = self._create_risk_exception()
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: Granting conditional approval
        conditional = workflow_repo["approve_exception"](exception_id, {
            "approver": "security.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "approval_type": "conditional",
            "conditions": [
                {
                    "requirement": "Implement additional logging",
                    "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "verification_method": "security_review"
                },
                {
                    "requirement": "Monthly security scans",
                    "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "verification_method": "automated_scan"
                }
            ],
            "comments": "Approved pending implementation of additional controls"
        })
        
        # Then: Conditional approval is tracked
        assert conditional["type"] == "Success"
        assert conditional["approval_type"] == "conditional"
        assert len(conditional["pending_conditions"]) == 2
        assert conditional["status"] == ExceptionStatus.PENDING_APPROVAL.value  # Still pending until conditions met
    
    def test_escalation_for_expired_approvals(self, workflow_repo):
        """SPEC: Expired approval requests escalate automatically"""
        # Given: Exception with SLA configuration
        request = self._create_risk_exception()
        request["approval_sla_hours"] = 48  # 48 hour SLA
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: Checking for expired approvals (simulating time passage)
        escalation_result = workflow_repo["check_approval_escalations"]({
            "as_of_date": (datetime.now() + timedelta(hours=49)).isoformat()
        })
        
        # Then: Should identify escalation needed
        assert escalation_result["type"] == "Success"
        assert exception_id in [e["exception_id"] for e in escalation_result["escalations"]]
        
        escalation = next(e for e in escalation_result["escalations"] if e["exception_id"] == exception_id)
        assert escalation["hours_overdue"] == 1
        assert escalation["escalated_to"] == "security.director@company.com"
        assert escalation["original_approver"] == "security.architect@company.com"
    
    def _create_risk_exception(self) -> Dict[str, Any]:
        """Helper to create risk exception requiring multiple approvals"""
        return {
            "requirement_id": "REQ-RISK-001",
            "type": ExceptionType.RISK_ACCEPTED.value,
            "justification": "Business critical functionality requires accepting identified security risk with compensating controls",
            "risk_assessment": "High risk requiring executive approval",
            "compensating_controls": ["Control A", "Control B", "Control C"],
            "business_impact": "Critical business function",
            "requestor": "product.owner@company.com"
        }


class TestAuditTrail:
    """Specification for complete audit trail of exception lifecycle"""
    
    def test_immutable_audit_trail_for_all_actions(self, workflow_repo):
        """SPEC: All exception actions create immutable audit records"""
        # Given: Exception going through full lifecycle
        request = {
            "requirement_id": "REQ-AUDIT-001",
            "type": ExceptionType.COMPENSATING_CONTROL.value,
            "justification": "Testing audit trail functionality with complete exception lifecycle demonstration",
            "risk_assessment": "Low risk for testing",
            "compensating_controls": ["Test control"],
            "business_impact": "None - testing",
            "requestor": "tester@company.com"
        }
        
        # Create exception
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # Update exception
        workflow_repo["update_exception"](exception_id, {
            "compensating_controls": ["Test control", "Additional control"],
            "updater": "tester@company.com"
        })
        
        # Add comment
        workflow_repo["add_exception_comment"](exception_id, {
            "author": "reviewer@company.com",
            "comment": "Please clarify the risk assessment",
            "visibility": "internal"
        })
        
        # Approve exception
        workflow_repo["approve_exception"](exception_id, {
            "approver": "security.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Approved with noted controls"
        })
        
        # When: Retrieving audit trail
        audit = workflow_repo["get_exception_audit_trail"](exception_id)
        
        # Then: Complete history is available
        assert audit["type"] == "Success"
        assert len(audit["events"]) >= 4  # Create, update, comment, approve
        
        # Verify audit event structure
        for event in audit["events"]:
            assert event["timestamp"] is not None
            assert event["event_type"] in [
                "exception_created",
                "exception_updated", 
                "comment_added",
                "exception_approved"
            ]
            assert event["actor"] is not None
            assert event["details"] is not None
            assert event["event_id"] is not None  # Unique identifier
            assert event["hash"] is not None  # Integrity hash
        
        # Verify chronological order
        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in audit["events"]]
        assert timestamps == sorted(timestamps)
        
        # Verify immutability - attempting to modify audit should fail
        modify_result = workflow_repo["modify_audit_event"](
            audit["events"][0]["event_id"],
            {"details": "Modified details"}
        )
        assert modify_result["type"] == "SecurityError"
        assert modify_result["code"] == "AUDIT_IMMUTABLE"
    
    def test_audit_trail_includes_all_metadata(self, workflow_repo):
        """SPEC: Audit events capture complete context and metadata"""
        # Given: Exception with approval
        request = self._create_simple_exception()
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # Approve with detailed metadata
        workflow_repo["approve_exception"](exception_id, {
            "approver": "security.architect@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Approved based on risk assessment",
            "client_ip": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "session_id": "sess_123456",
            "mfa_verified": True
        })
        
        # When: Checking audit trail
        audit = workflow_repo["get_exception_audit_trail"](exception_id)
        
        # Then: Metadata is preserved
        approval_event = next(e for e in audit["events"] if e["event_type"] == "exception_approved")
        assert approval_event["metadata"]["client_ip"] == "192.168.1.100"
        assert approval_event["metadata"]["mfa_verified"] is True
        assert approval_event["metadata"]["session_id"] == "sess_123456"
    
    def test_audit_export_formats(self, workflow_repo):
        """SPEC: Audit trails can be exported in multiple formats"""
        # Given: Exception with history
        request = self._create_simple_exception()
        create_result = workflow_repo["create_exception_request"](request)
        exception_id = create_result["exception_id"]
        
        # When: Exporting in different formats
        formats = ["json", "csv", "pdf", "blockchain"]
        
        for format_type in formats:
            export_result = workflow_repo["export_audit_trail"](exception_id, {
                "format": format_type,
                "include_metadata": True,
                "date_range": {
                    "start": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end": datetime.now().isoformat()
                }
            })
            
            # Then: Export succeeds with appropriate format
            assert export_result["type"] == "Success"
            assert export_result["format"] == format_type
            assert export_result["content"] is not None or export_result["url"] is not None
            
            if format_type == "blockchain":
                assert export_result["blockchain_hash"] is not None
                assert export_result["block_number"] is not None
    
    def test_audit_retention_and_archival(self, workflow_repo):
        """SPEC: Audit trails follow retention policies with archival"""
        # Given: Retention policy configuration
        policy_result = workflow_repo["set_audit_retention_policy"]({
            "active_retention_days": 365,  # 1 year active
            "archive_retention_years": 7,   # 7 years archived
            "deletion_requires_approval": True,
            "compliance_standards": ["SOX", "HIPAA"]
        })
        assert policy_result["type"] == "Success"
        
        # When: Checking old audit records
        archival_check = workflow_repo["check_audit_archival_status"]({
            "older_than_days": 366
        })
        
        # Then: Old records are identified for archival
        assert archival_check["type"] == "Success"
        assert archival_check["records_to_archive"] >= 0
        assert archival_check["archive_location"] in ["cold_storage", "glacier", "tape"]
        assert archival_check["estimated_cost"] is not None
    
    def _create_simple_exception(self) -> Dict[str, Any]:
        """Helper to create simple exception"""
        return {
            "requirement_id": "REQ-SIMPLE-001",
            "type": ExceptionType.NOT_APPLICABLE.value,
            "justification": "Standard does not apply to internal tooling used only by development team",
            "risk_assessment": "No risk - internal tool only",
            "compensating_controls": ["Internal use only"],
            "business_impact": "None",
            "requestor": "dev.lead@company.com"
        }


class TestPeriodicReviewReminders:
    """Specification for periodic review reminders and enforcement"""
    
    def test_automatic_review_reminders(self, workflow_repo):
        """SPEC: System automatically generates review reminders"""
        # Given: Exceptions with different review schedules
        exceptions = [
            {
                "requirement_id": "REQ-REVIEW-001",
                "type": ExceptionType.RISK_ACCEPTED.value,
                "justification": "Accepted risk requiring quarterly review for business critical system",
                "risk_assessment": "High risk requiring frequent review",
                "compensating_controls": ["Quarterly assessment"],
                "business_impact": "High",
                "requestor": "owner@company.com",
                "review_frequency_days": 90,  # Quarterly
                "last_review_date": (datetime.now() - timedelta(days=85)).isoformat()
            },
            {
                "requirement_id": "REQ-REVIEW-002",
                "type": ExceptionType.COMPENSATING_CONTROL.value,
                "justification": "Alternative controls in place requiring annual review for compliance",
                "risk_assessment": "Medium risk with stable controls",
                "compensating_controls": ["Annual audit"],
                "business_impact": "Medium",
                "requestor": "owner@company.com",
                "review_frequency_days": 365,  # Annual
                "last_review_date": (datetime.now() - timedelta(days=350)).isoformat()
            }
        ]
        
        exception_ids = []
        for exc in exceptions:
            result = workflow_repo["create_exception_request"](exc)
            exception_ids.append(result["exception_id"])
            # Approve to activate
            workflow_repo["approve_exception"](result["exception_id"], {
                "approver": "approver@company.com",
                "role": ApprovalLevel.SECURITY_ARCHITECT.value,
                "comments": "Approved"
            })
        
        # When: Checking for due reviews
        reminders = workflow_repo["get_review_reminders"]({
            "upcoming_days": 30,  # Reminders for reviews due in next 30 days
            "include_overdue": True
        })
        
        # Then: Both exceptions should have reminders
        assert reminders["type"] == "Success"
        assert len(reminders["reminders"]) >= 2
        
        # Verify reminder details
        for reminder in reminders["reminders"]:
            assert reminder["exception_id"] in exception_ids
            assert reminder["days_until_due"] is not None
            assert reminder["review_type"] in ["quarterly", "annual"]
            assert reminder["assigned_reviewer"] is not None
            assert reminder["last_review_date"] is not None
            
            if reminder["days_until_due"] < 0:
                assert reminder["is_overdue"] is True
                assert reminder["escalation_level"] > 0
    
    def test_review_workflow_enforcement(self, workflow_repo):
        """SPEC: Reviews follow structured workflow with documentation"""
        # Given: Exception due for review
        exc_result = workflow_repo["create_exception_request"]({
            "requirement_id": "REQ-REVIEW-003",
            "type": ExceptionType.RISK_ACCEPTED.value,
            "justification": "Risk accepted with periodic review requirement for regulatory compliance",
            "risk_assessment": "Ongoing risk requiring regular assessment",
            "compensating_controls": ["Monitoring"],
            "business_impact": "Medium",
            "requestor": "owner@company.com"
        })
        exception_id = exc_result["exception_id"]
        
        # Approve and trigger review
        workflow_repo["approve_exception"](exception_id, {
            "approver": "approver@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Approved"
        })
        
        # When: Starting review process
        review_start = workflow_repo["start_exception_review"](exception_id, {
            "reviewer": "security.reviewer@company.com",
            "review_type": "periodic_90_day",
            "checklist": [
                "Verify compensating controls still effective",
                "Assess current risk level",
                "Review business justification",
                "Check for security incidents"
            ]
        })
        
        assert review_start["type"] == "Success"
        assert review_start["review_id"] is not None
        assert review_start["status"] == "in_progress"
        
        # Complete review checklist
        for item in review_start["checklist_items"]:
            workflow_repo["complete_review_item"](review_start["review_id"], {
                "item_id": item["id"],
                "result": "pass",
                "notes": "Control verified effective",
                "evidence": ["screenshot_001.png", "report_q1.pdf"]
            })
        
        # When: Completing review with decision
        review_complete = workflow_repo["complete_exception_review"](review_start["review_id"], {
            "decision": "maintain",  # maintain, modify, revoke
            "rationale": "All controls remain effective, risk unchanged",
            "next_review_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "recommendations": [
                "Continue monthly monitoring",
                "Consider additional controls in Q3"
            ]
        })
        
        # Then: Review is recorded and next cycle scheduled
        assert review_complete["type"] == "Success"
        assert review_complete["review_completed"] is True
        assert review_complete["next_review_scheduled"] is True
        assert review_complete["decision"] == "maintain"
    
    def test_overdue_review_escalation(self, workflow_repo):
        """SPEC: Overdue reviews escalate through management chain"""
        # Given: Exception with overdue review
        exc_result = workflow_repo["create_exception_request"]({
            "requirement_id": "REQ-OVERDUE-001",
            "type": ExceptionType.RISK_ACCEPTED.value,
            "justification": "Testing overdue review escalation with high-risk exception requiring attention",
            "risk_assessment": "High risk",
            "compensating_controls": ["Control"],
            "business_impact": "High",
            "requestor": "owner@company.com",
            "review_frequency_days": 90,
            "last_review_date": (datetime.now() - timedelta(days=120)).isoformat()  # 30 days overdue
        })
        exception_id = exc_result["exception_id"]
        
        # Approve to activate
        workflow_repo["approve_exception"](exception_id, {
            "approver": "approver@company.com",
            "role": ApprovalLevel.SECURITY_ARCHITECT.value,
            "comments": "Approved"
        })
        
        # When: Processing escalations
        escalation = workflow_repo["process_review_escalations"]({
            "escalation_thresholds": {
                "level_1": 7,   # Manager after 7 days
                "level_2": 14,  # Director after 14 days
                "level_3": 30   # Executive after 30 days
            }
        })
        
        # Then: Exception is escalated to appropriate level
        assert escalation["type"] == "Success"
        assert exception_id in [e["exception_id"] for e in escalation["escalated_items"]]
        
        escalated = next(e for e in escalation["escalated_items"] if e["exception_id"] == exception_id)
        assert escalated["days_overdue"] == 30
        assert escalated["escalation_level"] == 3
        assert escalated["escalated_to"] == "ciso@company.com"
        assert escalated["original_reviewer"] == "security.reviewer@company.com"
        assert escalated["risk_score"] == "high"  # Prioritized by risk
    
    def test_review_reminder_customization(self, workflow_repo):
        """SPEC: Review reminders can be customized per exception type"""
        # Given: Custom reminder rules
        rules_result = workflow_repo["set_review_reminder_rules"]({
            "rules": [
                {
                    "exception_type": ExceptionType.RISK_ACCEPTED.value,
                    "reminder_schedule": [30, 14, 7, 1],  # Days before due
                    "include_stakeholders": ["risk_management", "business_owner"],
                    "require_pre_review": True
                },
                {
                    "exception_type": ExceptionType.COMPENSATING_CONTROL.value,
                    "reminder_schedule": [14, 7],
                    "include_stakeholders": ["security_architect"],
                    "require_pre_review": False
                },
                {
                    "exception_type": ExceptionType.TEMPORARY_WAIVER.value,
                    "reminder_schedule": [30, 14, 7, 3, 1],  # More frequent
                    "include_stakeholders": ["executive", "security_architect"],
                    "auto_expire_if_not_reviewed": True
                }
            ]
        })
        assert rules_result["type"] == "Success"
        
        # When: Generating reminders with custom rules
        reminders = workflow_repo["generate_custom_reminders"]({
            "run_date": datetime.now().isoformat()
        })
        
        # Then: Reminders follow custom schedules
        assert reminders["type"] == "Success"
        
        for reminder in reminders["generated_reminders"]:
            if reminder["exception_type"] == ExceptionType.RISK_ACCEPTED.value:
                assert reminder["requires_pre_review"] is True
                assert "risk_management" in reminder["recipients"]
            elif reminder["exception_type"] == ExceptionType.TEMPORARY_WAIVER.value:
                assert reminder["auto_expire_warning"] is not None
    
    def test_review_completion_metrics(self, workflow_repo):
        """SPEC: Track review completion rates and compliance"""
        # Given: Multiple exceptions with reviews
        # Create and complete some reviews, leave others pending
        
        # When: Generating review metrics
        metrics = workflow_repo["get_review_compliance_metrics"]({
            "period_start": (datetime.now() - timedelta(days=90)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "group_by": ["exception_type", "reviewer", "risk_level"]
        })
        
        # Then: Comprehensive metrics are available
        assert metrics["type"] == "Success"
        assert metrics["overall_compliance_rate"] is not None
        assert metrics["average_days_to_complete"] is not None
        assert metrics["overdue_count"] is not None
        
        # By exception type
        assert "by_exception_type" in metrics
        for exc_type in metrics["by_exception_type"]:
            assert "total_reviews_due" in exc_type
            assert "completed_on_time" in exc_type
            assert "completed_late" in exc_type
            assert "currently_overdue" in exc_type
            assert "compliance_rate" in exc_type


class TestExceptionMetricsAndReporting:
    """Specification for exception metrics and reporting capabilities"""
    
    def test_exception_usage_metrics(self, workflow_repo):
        """SPEC: Track comprehensive metrics on exception usage"""
        # Given: Various exceptions created over time
        # (Assuming test data exists)
        
        # When: Generating usage metrics
        metrics = workflow_repo["get_exception_metrics"]({
            "period_start": (datetime.now() - timedelta(days=365)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "include_trends": True
        })
        
        # Then: Comprehensive metrics are available
        assert metrics["type"] == "Success"
        
        # Overall statistics
        assert metrics["summary"]["total_exceptions"] >= 0
        assert metrics["summary"]["active_exceptions"] >= 0
        assert metrics["summary"]["expired_exceptions"] >= 0
        assert metrics["summary"]["revoked_exceptions"] >= 0
        
        # By type breakdown
        assert "by_type" in metrics
        for type_stat in metrics["by_type"]:
            assert type_stat["exception_type"] in [e.value for e in ExceptionType]
            assert type_stat["count"] >= 0
            assert type_stat["percentage"] >= 0
            assert type_stat["average_duration_days"] is not None
        
        # By risk level
        assert "by_risk_level" in metrics
        assert all(level in ["low", "medium", "high", "critical"] 
                  for level in metrics["by_risk_level"].keys())
        
        # Trends over time
        assert "trends" in metrics
        assert metrics["trends"]["monthly_creation_rate"] is not None
        assert metrics["trends"]["approval_rate"] is not None
        assert metrics["trends"]["rejection_rate"] is not None
    
    def test_exception_compliance_dashboard(self, workflow_repo):
        """SPEC: Generate compliance dashboard for exception status"""
        # When: Generating compliance dashboard
        dashboard = workflow_repo["generate_exception_dashboard"]({
            "as_of_date": datetime.now().isoformat(),
            "include_charts": True
        })
        
        # Then: Dashboard provides comprehensive view
        assert dashboard["type"] == "Success"
        
        # Key metrics
        assert dashboard["kpis"]["review_compliance_rate"] is not None
        assert dashboard["kpis"]["average_approval_time_hours"] is not None
        assert dashboard["kpis"]["exceptions_per_requirement_ratio"] is not None
        assert dashboard["kpis"]["high_risk_exception_count"] is not None
        
        # Alerts and warnings
        assert "alerts" in dashboard
        for alert in dashboard["alerts"]:
            assert alert["severity"] in ["info", "warning", "critical"]
            assert alert["message"] is not None
            assert alert["affected_exceptions"] is not None
            
        # Charts data
        if dashboard.get("charts"):
            assert "exception_trend_chart" in dashboard["charts"]
            assert "risk_distribution_pie" in dashboard["charts"]
            assert "approval_time_histogram" in dashboard["charts"]
    
    def test_exception_cost_analysis(self, workflow_repo):
        """SPEC: Analyze cost and resource impact of exceptions"""
        # When: Running cost analysis
        cost_analysis = workflow_repo["analyze_exception_costs"]({
            "period_start": (datetime.now() - timedelta(days=180)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "cost_factors": {
                "review_hour_cost": 150,  # $/hour for reviews
                "implementation_hour_cost": 200,  # $/hour for compensating controls
                "audit_cost_per_exception": 500,  # Fixed audit cost
                "risk_cost_multiplier": {
                    "low": 1.0,
                    "medium": 2.5,
                    "high": 5.0,
                    "critical": 10.0
                }
            }
        })
        
        # Then: Cost analysis is comprehensive
        assert cost_analysis["type"] == "Success"
        
        # Direct costs
        assert cost_analysis["direct_costs"]["total_review_cost"] >= 0
        assert cost_analysis["direct_costs"]["total_implementation_cost"] >= 0
        assert cost_analysis["direct_costs"]["total_audit_cost"] >= 0
        
        # Risk-adjusted costs
        assert cost_analysis["risk_adjusted_costs"]["total"] >= 0
        assert cost_analysis["risk_adjusted_costs"]["by_risk_level"] is not None
        
        # Cost trends
        assert cost_analysis["trends"]["monthly_average_cost"] is not None
        assert cost_analysis["trends"]["cost_per_exception"] is not None
        
        # Recommendations
        assert "cost_reduction_recommendations" in cost_analysis
    
    def test_exception_pattern_detection(self, workflow_repo):
        """SPEC: Detect patterns and anomalies in exception usage"""
        # When: Running pattern analysis
        patterns = workflow_repo["analyze_exception_patterns"]({
            "analysis_period_days": 180,
            "pattern_types": [
                "clustering",      # Similar exceptions
                "temporal",        # Time-based patterns
                "organizational",  # By team/department
                "risk_correlation" # Risk factor correlation
            ]
        })
        
        # Then: Patterns are identified
        assert patterns["type"] == "Success"
        
        # Clustering patterns
        assert "clusters" in patterns
        for cluster in patterns["clusters"]:
            assert cluster["cluster_id"] is not None
            assert cluster["size"] >= 2
            assert cluster["common_attributes"] is not None
            assert cluster["recommendation"] is not None
        
        # Temporal patterns
        assert "temporal_patterns" in patterns
        assert patterns["temporal_patterns"]["peak_periods"] is not None
        assert patterns["temporal_patterns"]["seasonality"] in [None, "quarterly", "annual"]
        
        # Organizational patterns
        assert "organizational_patterns" in patterns
        for org_pattern in patterns["organizational_patterns"]:
            assert org_pattern["department"] is not None
            assert org_pattern["exception_rate"] is not None
            assert org_pattern["common_types"] is not None
        
        # Anomaly detection
        assert "anomalies" in patterns
        for anomaly in patterns["anomalies"]:
            assert anomaly["type"] in ["spike", "unusual_pattern", "policy_violation"]
            assert anomaly["confidence"] >= 0.0 and anomaly["confidence"] <= 1.0
            assert anomaly["recommendation"] is not None
    
    def test_executive_exception_report(self, workflow_repo):
        """SPEC: Generate executive-level exception reports"""
        # When: Generating executive report
        exec_report = workflow_repo["generate_executive_report"]({
            "report_period": "quarterly",
            "quarter": "Q4",
            "year": 2023,
            "include_projections": True,
            "compare_to_previous": True
        })
        
        # Then: Report is executive-appropriate
        assert exec_report["type"] == "Success"
        
        # Executive summary
        assert exec_report["executive_summary"]["total_exceptions"] is not None
        assert exec_report["executive_summary"]["risk_exposure_score"] is not None
        assert exec_report["executive_summary"]["compliance_score"] is not None
        assert exec_report["executive_summary"]["key_concerns"] is not None
        
        # Comparison to previous period
        if exec_report.get("comparison"):
            assert exec_report["comparison"]["exception_change_percent"] is not None
            assert exec_report["comparison"]["risk_trend"] in ["increasing", "stable", "decreasing"]
            assert exec_report["comparison"]["notable_changes"] is not None
        
        # Projections
        if exec_report.get("projections"):
            assert exec_report["projections"]["next_quarter_estimate"] is not None
            assert exec_report["projections"]["risk_areas"] is not None
            assert exec_report["projections"]["resource_needs"] is not None
        
        # Recommendations
        assert len(exec_report["recommendations"]) > 0
        for rec in exec_report["recommendations"]:
            assert rec["priority"] in ["low", "medium", "high", "critical"]
            assert rec["action"] is not None
            assert rec["expected_impact"] is not None
            assert rec["timeline"] is not None
    
    def test_automated_exception_alerts(self, workflow_repo):
        """SPEC: Configure automated alerts for exception conditions"""
        # Given: Alert configuration
        alert_config = workflow_repo["configure_exception_alerts"]({
            "alerts": [
                {
                    "name": "high_risk_concentration",
                    "condition": "high_risk_exceptions > 10",
                    "severity": "critical",
                    "recipients": ["ciso@company.com", "risk@company.com"],
                    "frequency": "daily"
                },
                {
                    "name": "review_compliance_drop",
                    "condition": "review_compliance_rate < 0.8",
                    "severity": "warning",
                    "recipients": ["security.team@company.com"],
                    "frequency": "weekly"
                },
                {
                    "name": "exception_spike",
                    "condition": "weekly_exceptions > average * 2",
                    "severity": "warning",
                    "recipients": ["security.architect@company.com"],
                    "frequency": "real_time"
                }
            ]
        })
        assert alert_config["type"] == "Success"
        
        # When: Checking for triggered alerts
        alerts = workflow_repo["check_exception_alerts"]({
            "as_of": datetime.now().isoformat()
        })
        
        # Then: Alerts are evaluated and triggered appropriately
        assert alerts["type"] == "Success"
        assert "triggered_alerts" in alerts
        
        for alert in alerts["triggered_alerts"]:
            assert alert["alert_name"] is not None
            assert alert["condition_met"] is True
            assert alert["current_value"] is not None
            assert alert["threshold_value"] is not None
            assert alert["notification_sent"] is not None


@pytest.fixture
def workflow_repo():
    """Create a test repository with exception workflow capabilities"""
    from poc.uri.enforced_workflow import create_workflow_repository
    import os
    
    # Set environment variable to skip schema check
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "1"
    
    # Create in-memory workflow repository with exception extensions
    base_repo = create_workflow_repository(":memory:")
    
    # Add exception workflow methods (these would be implemented in the actual system)
    exception_methods = {
        "create_exception_request": lambda req: _mock_create_exception(req),
        "approve_exception": lambda id, data: _mock_approve_exception(id, data),
        "reject_exception": lambda id, data: _mock_reject_exception(id, data),
        "update_exception": lambda id, data: _mock_update_exception(id, data),
        "get_exception_audit_trail": lambda id: _mock_get_audit_trail(id),
        "add_exception_comment": lambda id, data: _mock_add_comment(id, data),
        "delegate_approval": lambda id, data: _mock_delegate_approval(id, data),
        "check_approval_escalations": lambda criteria: _mock_check_escalations(criteria),
        "modify_audit_event": lambda id, data: {"type": "SecurityError", "code": "AUDIT_IMMUTABLE"},
        "export_audit_trail": lambda id, opts: _mock_export_audit(id, opts),
        "set_audit_retention_policy": lambda policy: {"type": "Success"},
        "check_audit_archival_status": lambda criteria: _mock_check_archival(criteria),
        "get_review_reminders": lambda opts: _mock_get_reminders(opts),
        "start_exception_review": lambda id, data: _mock_start_review(id, data),
        "complete_review_item": lambda id, data: {"type": "Success"},
        "complete_exception_review": lambda id, data: _mock_complete_review(id, data),
        "process_review_escalations": lambda opts: _mock_process_escalations(opts),
        "set_review_reminder_rules": lambda rules: {"type": "Success"},
        "generate_custom_reminders": lambda opts: _mock_generate_reminders(opts),
        "get_review_compliance_metrics": lambda opts: _mock_review_metrics(opts),
        "get_exception_metrics": lambda opts: _mock_exception_metrics(opts),
        "generate_exception_dashboard": lambda opts: _mock_generate_dashboard(opts),
        "analyze_exception_costs": lambda opts: _mock_cost_analysis(opts),
        "analyze_exception_patterns": lambda opts: _mock_pattern_analysis(opts),
        "generate_executive_report": lambda opts: _mock_executive_report(opts),
        "configure_exception_alerts": lambda config: {"type": "Success"},
        "check_exception_alerts": lambda opts: _mock_check_alerts(opts),
    }
    
    # Merge with base repository
    return {**base_repo, **exception_methods}


# Mock implementations for testing
def _mock_create_exception(request):
    """Mock exception creation"""
    # Validate required fields
    required = ["requirement_id", "type", "justification", "risk_assessment", 
                "compensating_controls", "business_impact", "requestor"]
    missing = [f for f in required if f not in request]
    
    if missing:
        return {
            "type": "ValidationError",
            "code": "MISSING_REQUIRED_FIELDS",
            "missing_fields": missing
        }
    
    # Check justification length
    if len(request["justification"]) < 50:
        return {
            "type": "ValidationError",
            "code": "INSUFFICIENT_JUSTIFICATION",
            "minimum_length": 50,
            "provided_length": len(request["justification"])
        }
    
    # Check temporary exceptions have expiration
    if request["type"] == ExceptionType.TEMPORARY_WAIVER.value and "expiration_date" not in request:
        return {
            "type": "ValidationError",
            "code": "EXPIRATION_REQUIRED",
            "message": "Temporary exceptions must have expiration date"
        }
    
    # Determine approval requirements
    approval_map = {
        ExceptionType.NOT_APPLICABLE.value: [ApprovalLevel.TEAM_LEAD.value],
        ExceptionType.COMPENSATING_CONTROL.value: [ApprovalLevel.SECURITY_ARCHITECT.value],
        ExceptionType.RISK_ACCEPTED.value: [
            ApprovalLevel.SECURITY_ARCHITECT.value,
            ApprovalLevel.RISK_MANAGEMENT.value
        ],
        ExceptionType.TEMPORARY_WAIVER.value: [
            ApprovalLevel.SECURITY_ARCHITECT.value,
            ApprovalLevel.EXECUTIVE.value
        ]
    }
    
    return {
        "type": "Success",
        "exception_id": f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": ExceptionStatus.PENDING_APPROVAL.value,
        "created_at": datetime.now().isoformat(),
        "approval_required": approval_map.get(request["type"], [ApprovalLevel.SECURITY_ARCHITECT.value])
    }


def _mock_approve_exception(exception_id, data):
    """Mock exception approval"""
    # Mock validation and state management
    return {
        "type": "Success",
        "status": ExceptionStatus.APPROVED.value,
        "remaining_approvals": [],
        "timestamp": datetime.now().isoformat()
    }


def _mock_reject_exception(exception_id, data):
    """Mock exception rejection"""
    return {
        "type": "Success",
        "status": ExceptionStatus.REJECTED.value,
        "can_resubmit": True,
        "resubmission_requirements": ["Address rejection reasons"]
    }


def _mock_update_exception(exception_id, data):
    """Mock exception update"""
    return {"type": "Success"}


def _mock_get_audit_trail(exception_id):
    """Mock audit trail retrieval"""
    return {
        "type": "Success",
        "events": [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "exception_created",
                "actor": "tester@company.com",
                "details": {"action": "created"},
                "event_id": "evt_001",
                "hash": "abc123",
                "metadata": {}
            }
        ]
    }


def _mock_add_comment(exception_id, data):
    """Mock adding comment"""
    return {"type": "Success"}


def _mock_delegate_approval(exception_id, data):
    """Mock approval delegation"""
    return {
        "type": "Success",
        "delegation_id": f"DEL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }


def _mock_check_escalations(criteria):
    """Mock escalation check"""
    return {
        "type": "Success",
        "escalations": []
    }


def _mock_export_audit(exception_id, options):
    """Mock audit export"""
    format_type = options["format"]
    result = {
        "type": "Success",
        "format": format_type,
        "content": f"Mock {format_type} content"
    }
    
    if format_type == "blockchain":
        result["blockchain_hash"] = "0x123abc"
        result["block_number"] = 12345
    
    return result


def _mock_check_archival(criteria):
    """Mock archival check"""
    return {
        "type": "Success",
        "records_to_archive": 42,
        "archive_location": "cold_storage",
        "estimated_cost": 125.50
    }


def _mock_get_reminders(options):
    """Mock review reminders"""
    return {
        "type": "Success",
        "reminders": []
    }


def _mock_start_review(exception_id, data):
    """Mock review start"""
    return {
        "type": "Success",
        "review_id": f"REV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": "in_progress",
        "checklist_items": [
            {"id": "item_1", "description": "Verify controls"}
        ]
    }


def _mock_complete_review(review_id, data):
    """Mock review completion"""
    return {
        "type": "Success",
        "review_completed": True,
        "next_review_scheduled": True,
        "decision": data["decision"]
    }


def _mock_process_escalations(options):
    """Mock escalation processing"""
    return {
        "type": "Success",
        "escalated_items": []
    }


def _mock_generate_reminders(options):
    """Mock custom reminders"""
    return {
        "type": "Success",
        "generated_reminders": []
    }


def _mock_review_metrics(options):
    """Mock review metrics"""
    return {
        "type": "Success",
        "overall_compliance_rate": 0.85,
        "average_days_to_complete": 5.2,
        "overdue_count": 3,
        "by_exception_type": []
    }


def _mock_exception_metrics(options):
    """Mock exception metrics"""
    return {
        "type": "Success",
        "summary": {
            "total_exceptions": 100,
            "active_exceptions": 75,
            "expired_exceptions": 20,
            "revoked_exceptions": 5
        },
        "by_type": [],
        "by_risk_level": {
            "low": 40,
            "medium": 35,
            "high": 20,
            "critical": 5
        },
        "trends": {
            "monthly_creation_rate": 8.5,
            "approval_rate": 0.92,
            "rejection_rate": 0.08
        }
    }


def _mock_generate_dashboard(options):
    """Mock dashboard generation"""
    return {
        "type": "Success",
        "kpis": {
            "review_compliance_rate": 0.87,
            "average_approval_time_hours": 48.5,
            "exceptions_per_requirement_ratio": 0.15,
            "high_risk_exception_count": 12
        },
        "alerts": [],
        "charts": {
            "exception_trend_chart": {},
            "risk_distribution_pie": {},
            "approval_time_histogram": {}
        }
    }


def _mock_cost_analysis(options):
    """Mock cost analysis"""
    return {
        "type": "Success",
        "direct_costs": {
            "total_review_cost": 15000,
            "total_implementation_cost": 45000,
            "total_audit_cost": 10000
        },
        "risk_adjusted_costs": {
            "total": 125000,
            "by_risk_level": {}
        },
        "trends": {
            "monthly_average_cost": 11667,
            "cost_per_exception": 1250
        },
        "cost_reduction_recommendations": []
    }


def _mock_pattern_analysis(options):
    """Mock pattern analysis"""
    return {
        "type": "Success",
        "clusters": [],
        "temporal_patterns": {
            "peak_periods": ["Q4", "Q2"],
            "seasonality": "quarterly"
        },
        "organizational_patterns": [],
        "anomalies": []
    }


def _mock_executive_report(options):
    """Mock executive report"""
    return {
        "type": "Success",
        "executive_summary": {
            "total_exceptions": 100,
            "risk_exposure_score": 6.8,
            "compliance_score": 8.5,
            "key_concerns": ["High risk concentration"]
        },
        "comparison": {
            "exception_change_percent": 12.5,
            "risk_trend": "increasing",
            "notable_changes": ["More risk accepted exceptions"]
        },
        "projections": {
            "next_quarter_estimate": 110,
            "risk_areas": ["Authentication", "Data protection"],
            "resource_needs": ["Additional security reviewers"]
        },
        "recommendations": [
            {
                "priority": "high",
                "action": "Increase review frequency",
                "expected_impact": "Reduce risk by 20%",
                "timeline": "Q1 2024"
            }
        ]
    }


def _mock_check_alerts(options):
    """Mock alert checking"""
    return {
        "type": "Success",
        "triggered_alerts": []
    }