#!/usr/bin/env python3
"""
Demo: Enforced Reference Guardrails System

This demonstration showcases the complete enforced reference system including:
1. Mandatory reference selection for requirements
2. Exception workflows with approval process
3. Audit trail tracking
4. Completeness analysis and reporting
5. Real-world usage scenarios
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from reference_repository import create_reference_repository
from asvs_loader import ASVSLoader
from enforced_workflow import EnforcedRequirementWorkflow
from test_completeness_report import TestCompletenessAnalyzer


class GuardrailsDemo:
    """Interactive demonstration of the enforced reference system"""
    
    def __init__(self):
        """Initialize demo with in-memory database"""
        self.db_path = ":memory:"
        self._setup_system()
        
    def _setup_system(self):
        """Set up the complete system"""
        print("🚀 Initializing Enforced Reference Guardrails System...")
        print("=" * 60)
        
        # Create repository
        repo_result = create_reference_repository(self.db_path)
        if repo_result["type"] != "Success":
            raise Exception(f"Failed to create repository: {repo_result}")
        self.repo = repo_result["value"]
        
        # Load ASVS references
        print("\n📚 Loading ASVS 4.0.3 references...")
        loader = ASVSLoader(self.repo)
        asvs_result = loader.load_asvs_data()
        if asvs_result["type"] != "Success":
            raise Exception(f"Failed to load ASVS: {asvs_result}")
        print(f"✅ Loaded {asvs_result['value']['loaded_count']} ASVS references")
        
        # Initialize enforced workflow
        self.workflow = EnforcedRequirementWorkflow(self.repo)
        
        # Initialize analyzer
        conn = self.repo["_connection"]()
        self.analyzer = TestCompletenessAnalyzer(conn)
        
        print("\n✅ System initialized successfully!")
    
    def demo_mandatory_reference_selection(self):
        """Demonstrate mandatory reference selection"""
        print("\n\n🎯 Demo 1: Mandatory Reference Selection")
        print("=" * 60)
        print("Creating an authentication requirement with proper references...")
        
        # Define requirement
        requirement = {
            "uri": "req://webapp/auth/password-validation",
            "title": "Password Validation Service",
            "description": "Implement secure password validation with complexity rules",
            "entity_type": "requirement",
            "metadata": {
                "category": "authentication",
                "project": "webapp",
                "priority": "high",
                "sprint": "2024-Q1"
            }
        }
        
        # Select relevant ASVS references
        selected_references = [
            "asvs-v4.0.3-2.1.1",  # Minimum password length
            "asvs-v4.0.3-2.1.2",  # No common passwords
            "asvs-v4.0.3-2.1.3",  # No truncation
            "asvs-v4.0.3-2.1.7"   # Minimum complexity
        ]
        
        print(f"\n📋 Requirement: {requirement['title']}")
        print(f"📍 URI: {requirement['uri']}")
        print(f"\n🔗 Selected ASVS References:")
        for ref in selected_references:
            ref_data = self.repo["find"](ref)
            if ref_data["type"] == "Success":
                ref_info = ref_data["value"]
                print(f"   - {ref}: {ref_info.get('description', 'N/A')}")
        
        # Create requirement with references
        print("\n⚡ Creating requirement with enforced references...")
        result = self.workflow.create_requirement(requirement, selected_references)
        
        if result["type"] == "Success":
            print("✅ Requirement created successfully!")
            print(f"   - Requirement ID: {result['value']['requirement_id']}")
            print(f"   - References linked: {len(result['value']['references'])}")
            print(f"   - Audit logged: Yes")
        else:
            print(f"❌ Failed: {result}")
    
    def demo_rejection_without_references(self):
        """Demonstrate rejection when references are missing"""
        print("\n\n🚫 Demo 2: Rejection Without References")
        print("=" * 60)
        print("Attempting to create a requirement without references...")
        
        requirement = {
            "uri": "req://webapp/session/token-generation",
            "title": "Session Token Generation",
            "description": "Generate secure session tokens",
            "entity_type": "requirement",
            "metadata": {
                "category": "session",
                "project": "webapp"
            }
        }
        
        print(f"\n📋 Requirement: {requirement['title']}")
        print("🔗 Selected References: None (testing rejection)")
        
        print("\n⚡ Attempting to create without references...")
        result = self.workflow.create_requirement(requirement, [])
        
        if result["type"] == "ValidationError":
            print("✅ Correctly rejected!")
            print(f"   - Error: {result['error']['message']}")
            print("   - Category 'session' requires ASVS references")
            print("\n💡 Suggestion: Use these references:")
            print("   - asvs-v4.0.3-3.2.1: Secure token generation")
            print("   - asvs-v4.0.3-3.2.2: Sufficient entropy")
    
    def demo_exception_workflow(self):
        """Demonstrate exception workflow for special cases"""
        print("\n\n🔄 Demo 3: Exception Workflow")
        print("=" * 60)
        print("Creating a requirement for a legacy system with exception...")
        
        requirement = {
            "uri": "req://legacy/auth/basic-auth",
            "title": "Legacy Basic Authentication",
            "description": "Maintain basic auth for legacy API (migration planned)",
            "entity_type": "requirement",
            "metadata": {
                "category": "authentication",
                "project": "legacy-api",
                "system_type": "legacy"
            }
        }
        
        exception_data = {
            "reason": "legacy_system",
            "justification": "Legacy system scheduled for migration Q3 2024. Basic auth required for backward compatibility.",
            "approver": "security-architect",
            "risk_accepted": True,
            "mitigation": "API Gateway rate limiting, IP allowlist, monitoring alerts",
            "review_date": "2024-07-01"
        }
        
        print(f"\n📋 Requirement: {requirement['title']}")
        print(f"⚠️  Exception Reason: {exception_data['reason']}")
        print(f"📝 Justification: {exception_data['justification']}")
        print(f"🛡️  Mitigation: {exception_data['mitigation']}")
        
        print("\n⚡ Creating requirement with exception...")
        result = self.workflow.create_requirement(
            requirement,
            selected_references=None,
            exception_data=exception_data
        )
        
        if result["type"] == "PendingApproval":
            print("⏳ Exception request created - Pending approval")
            exception_id = result["value"]["exception_id"]
            print(f"   - Exception ID: {exception_id}")
            print(f"   - Status: {result['value']['status']}")
            
            # Simulate approval
            print("\n👤 Security Architect reviewing exception...")
            approval_result = self.workflow.approve_exception(
                exception_id,
                "security-architect",
                "Approved with documented mitigations. Review in Q3."
            )
            
            if approval_result["type"] == "Success":
                print("✅ Exception approved!")
                print(f"   - Requirement created: {approval_result['value']['requirement_id']}")
                print("   - Risk accepted with mitigations")
                print("   - Review scheduled for Q3 2024")
    
    def demo_completeness_analysis(self):
        """Demonstrate completeness analysis and reporting"""
        print("\n\n📊 Demo 4: Completeness Analysis")
        print("=" * 60)
        
        # First, create more requirements for analysis
        print("Creating additional requirements for analysis...")
        
        test_requirements = [
            {
                "req": {
                    "uri": "req://webapp/crypto/tls-config",
                    "title": "TLS Configuration",
                    "description": "Secure TLS configuration for all endpoints",
                    "entity_type": "requirement",
                    "metadata": {"category": "cryptography", "project": "webapp"}
                },
                "refs": ["asvs-v4.0.3-9.1.1", "asvs-v4.0.3-9.1.2"]
            },
            {
                "req": {
                    "uri": "req://webapp/access/rbac-implementation",
                    "title": "Role-Based Access Control",
                    "description": "Implement RBAC for all resources",
                    "entity_type": "requirement",
                    "metadata": {"category": "access_control", "project": "webapp"}
                },
                "refs": ["asvs-v4.0.3-4.1.3", "asvs-v4.0.3-4.1.4"]
            }
        ]
        
        for item in test_requirements:
            result = self.workflow.create_requirement(item["req"], item["refs"])
            if result["type"] == "Success":
                print(f"✅ Created: {item['req']['title']}")
        
        # Analyze completeness
        print("\n📈 Analyzing completeness...")
        
        # Category analysis
        category_analysis = self.analyzer.analyze_category_completeness()
        print("\n📊 Category Coverage:")
        for category, data in sorted(category_analysis.items()):
            coverage = data['coverage_percentage']
            status = data['status']
            bar = "█" * int(coverage / 10) + "░" * (10 - int(coverage / 10))
            print(f"   {category:20} [{bar}] {coverage:5.1f}% - {status}")
        
        # Project coverage
        project_coverage = self.analyzer.analyze_project_coverage()
        overall = project_coverage['overall']
        print(f"\n📊 Overall Project Coverage:")
        print(f"   Grade: {overall['grade']}")
        print(f"   Coverage: {overall['coverage_percentage']:.1f}%")
        print(f"   Total Requirements: {overall['total_requirements']}")
        print(f"   Implemented: {overall['implemented_requirements']}")
        
        # Risk assessment
        risk = project_coverage['risk_assessment']
        print(f"\n⚠️  Risk Assessment:")
        print(f"   Level: {risk['level'].upper()}")
        print(f"   Description: {risk['description']}")
        
        # Top gaps
        gaps = self.analyzer.identify_gaps_with_priority()
        print(f"\n🎯 Top Priority Gaps:")
        for i, gap in enumerate(gaps[:5], 1):
            print(f"   {i}. {gap['id']} (Priority: {gap['priority_score']})")
            print(f"      {gap['description']}")
            print(f"      Category: {gap['category']} | Level: {gap['level']}")
    
    def demo_audit_trail(self):
        """Demonstrate audit trail functionality"""
        print("\n\n📜 Demo 5: Audit Trail")
        print("=" * 60)
        
        print("Retrieving audit trail for all operations...")
        
        # Get all audit entries
        all_entries = self.workflow.audit_logger.get_all_entries()
        
        print(f"\n📊 Total Audit Entries: {len(all_entries)}")
        print("\n📜 Recent Audit Trail:")
        
        # Show last 10 entries
        for entry in all_entries[-10:]:
            timestamp = entry['timestamp']
            action = entry['action']
            req_id = entry.get('requirement_id', 'N/A')
            user = entry.get('user', entry.get('approver', 'system'))
            
            # Format based on action
            if action == "requirement_created":
                icon = "✅"
                desc = f"Requirement created: {req_id}"
            elif action == "references_enforced":
                icon = "🔗"
                desc = f"References linked: {entry.get('reference_count', 0)} refs"
            elif action == "exception_requested":
                icon = "⚠️"
                desc = f"Exception requested: {entry.get('reason', 'N/A')}"
            elif action == "exception_approved":
                icon = "✓"
                desc = "Exception approved"
            else:
                icon = "•"
                desc = action
            
            print(f"   {icon} [{timestamp[:19]}] {user:15} | {desc}")
        
        # Summary statistics
        print(f"\n📊 Audit Summary:")
        action_counts = {}
        for entry in all_entries:
            action = entry['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in sorted(action_counts.items()):
            print(f"   - {action}: {count}")
    
    def demo_export_reports(self):
        """Demonstrate report export functionality"""
        print("\n\n💾 Demo 6: Export Reports")
        print("=" * 60)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export different formats
            json_path = Path(temp_dir) / "completeness_report.json"
            html_path = Path(temp_dir) / "completeness_report.html"
            csv_path = Path(temp_dir) / "completeness_report.csv"
            
            print("Exporting reports in multiple formats...")
            
            # JSON export
            self.analyzer.export_json(str(json_path))
            print(f"✅ JSON report: {json_path.name} ({json_path.stat().st_size:,} bytes)")
            
            # HTML export
            self.analyzer.export_html(str(html_path))
            print(f"✅ HTML report: {html_path.name} ({html_path.stat().st_size:,} bytes)")
            
            # CSV export
            self.analyzer.export_csv(str(csv_path))
            categories_csv = csv_path.with_suffix('').with_suffix('_categories.csv')
            gaps_csv = csv_path.with_suffix('').with_suffix('_gaps.csv')
            print(f"✅ CSV reports:")
            print(f"   - Categories: {categories_csv.name} ({categories_csv.stat().st_size:,} bytes)")
            print(f"   - Gaps: {gaps_csv.name} ({gaps_csv.stat().st_size:,} bytes)")
            
            # Show sample of JSON report
            with open(json_path, 'r') as f:
                report_data = json.load(f)
            
            print(f"\n📄 Report Summary:")
            print(f"   Generated: {report_data['metadata']['timestamp'][:19]}")
            print(f"   Categories analyzed: {len(report_data['category_analysis'])}")
            print(f"   Gaps identified: {len(report_data['gap_analysis'])}")
            print(f"   Overall grade: {report_data['project_coverage']['overall']['grade']}")
    
    def run_all_demos(self):
        """Run all demonstrations"""
        demos = [
            ("Mandatory Reference Selection", self.demo_mandatory_reference_selection),
            ("Rejection Without References", self.demo_rejection_without_references),
            ("Exception Workflow", self.demo_exception_workflow),
            ("Completeness Analysis", self.demo_completeness_analysis),
            ("Audit Trail", self.demo_audit_trail),
            ("Export Reports", self.demo_export_reports)
        ]
        
        print("\n🚀 Running Complete Enforced Reference Guardrails Demo")
        print("=" * 60)
        
        for i, (name, demo_func) in enumerate(demos, 1):
            try:
                demo_func()
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
        
        print("\n\n✅ Demo Complete!")
        print("=" * 60)
        print("\n🎯 Key Takeaways:")
        print("1. Requirements MUST be linked to reference standards")
        print("2. Exceptions require justification and approval")
        print("3. All actions are audited for compliance")
        print("4. Completeness tracking ensures coverage")
        print("5. Multiple export formats support different use cases")
        print("\n💡 This enforces security-by-design principles!")


def main():
    """Run the complete demonstration"""
    demo = GuardrailsDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()