#!/usr/bin/env python3
"""
Demo: Mandatory Reference Validation

Shows how to use the mandatory reference validation system to ensure
requirements have appropriate standard references based on their category.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List
import kuzu

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_mandatory_references import MandatoryReferenceConfig
from reference_repository import create_reference_repository


def setup_demo_database():
    """Create a demo database with sample requirements and references"""
    # Create in-memory database
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Create schema
    print("Setting up database schema...")
    conn.execute("""
    CREATE NODE TABLE RequirementEntity (
        uri STRING PRIMARY KEY,
        title STRING,
        description STRING,
        category STRING,
        priority STRING,
        status STRING DEFAULT 'draft',
        created_date STRING
    )
    """)
    
    conn.execute("""
    CREATE NODE TABLE ReferenceEntity (
        id STRING PRIMARY KEY,
        standard STRING,
        version STRING,
        section STRING,
        description STRING,
        level INT64,
        category STRING
    )
    """)
    
    conn.execute("""
    CREATE REL TABLE IMPLEMENTS (
        FROM RequirementEntity TO ReferenceEntity,
        status STRING DEFAULT 'planned',
        justification STRING,
        verified_date STRING
    )
    """)
    
    print("Schema created successfully.\n")
    return conn


def load_sample_data(conn):
    """Load sample requirements and references"""
    print("Loading sample requirements...")
    
    # Sample requirements across different categories
    requirements = [
        # Well-documented authentication requirements
        {
            "uri": "req:app:auth:001",
            "title": "Secure User Authentication",
            "description": "Implement secure password-based authentication with proper validation",
            "category": "authentication",
            "priority": "high",
            "references": ["ASVS_V2.1.1", "NIST_5.1.1"]
        },
        {
            "uri": "req:app:auth:002",
            "title": "Multi-Factor Authentication",
            "description": "Support MFA for privileged accounts",
            "category": "authentication", 
            "priority": "high",
            "references": ["ASVS_V2.8.1", "NIST_5.1.4"]
        },
        
        # Authorization requirement missing references
        {
            "uri": "req:app:authz:001",
            "title": "Role-Based Access Control",
            "description": "Implement RBAC for application resources",
            "category": "authorization",
            "priority": "high",
            "references": []  # Missing mandatory references!
        },
        
        # Cryptography requirement with partial references
        {
            "uri": "req:app:crypto:001",
            "title": "Data Encryption at Rest",
            "description": "Encrypt sensitive data using AES-256",
            "category": "cryptography",
            "priority": "critical",
            "references": ["ASVS_V6.2.1"]  # Missing NIST and FIPS references!
        },
        
        # POC requirement (should be exempt)
        {
            "uri": "req:project:poc:newfeature:001",
            "title": "Experimental Authentication Method",
            "description": "Test new biometric authentication approach",
            "category": "authentication",
            "priority": "low",
            "references": []  # OK for POC
        },
        
        # Data protection requirement
        {
            "uri": "req:app:data:001",
            "title": "GDPR Compliance for User Data",
            "description": "Ensure user data handling complies with GDPR",
            "category": "data_protection",
            "priority": "high",
            "references": ["GDPR_Art32", "ISO_A8.2", "ASVS_V8.1.1"]
        },
        
        # API security requirement
        {
            "uri": "req:app:api:001",
            "title": "API Rate Limiting",
            "description": "Implement rate limiting for all API endpoints",
            "category": "api_security",
            "priority": "medium",
            "references": ["ASVS_V13.2.1"]  # Missing OWASP API reference
        }
    ]
    
    # Sample reference standards
    references = [
        # ASVS References
        {"id": "ASVS_V2.1.1", "standard": "OWASP ASVS", "version": "4.0.3", 
         "section": "V2.1", "description": "Password Security Requirements"},
        {"id": "ASVS_V2.8.1", "standard": "OWASP ASVS", "version": "4.0.3",
         "section": "V2.8", "description": "Multi-Factor Authentication"},
        {"id": "ASVS_V4.1.1", "standard": "OWASP ASVS", "version": "4.0.3",
         "section": "V4.1", "description": "General Access Control Design"},
        {"id": "ASVS_V6.2.1", "standard": "OWASP ASVS", "version": "4.0.3",
         "section": "V6.2", "description": "Algorithms"},
        {"id": "ASVS_V8.1.1", "standard": "OWASP ASVS", "version": "4.0.3",
         "section": "V8.1", "description": "General Data Protection"},
        {"id": "ASVS_V13.2.1", "standard": "OWASP ASVS", "version": "4.0.3",
         "section": "V13.2", "description": "RESTful Web Service Verification"},
        
        # NIST References
        {"id": "NIST_5.1.1", "standard": "NIST 800-63B", "version": "3",
         "section": "5.1", "description": "Memorized Secret Authenticators"},
        {"id": "NIST_5.1.4", "standard": "NIST 800-63B", "version": "3",
         "section": "5.1", "description": "Multi-Factor Authentication"},
        
        # ISO 27001 References
        {"id": "ISO_A8.2", "standard": "ISO27001", "version": "2022",
         "section": "A.8", "description": "Information Classification"},
        {"id": "ISO_A9.1", "standard": "ISO27001", "version": "2022",
         "section": "A.9", "description": "Access Control Policy"},
        
        # GDPR References
        {"id": "GDPR_Art32", "standard": "GDPR", "version": "2018",
         "section": "Article 32", "description": "Security of Processing"},
         
        # OWASP API References
        {"id": "OWASP_API_4", "standard": "OWASP API Security", "version": "2023",
         "section": "API4", "description": "Unrestricted Resource Consumption"}
    ]
    
    # Insert requirements
    for req in requirements:
        conn.execute("""
        CREATE (r:RequirementEntity {
            uri: $uri,
            title: $title,
            description: $description,
            category: $category,
            priority: $priority,
            status: 'active'
        })
        """, {
            "uri": req["uri"],
            "title": req["title"],
            "description": req["description"],
            "category": req["category"],
            "priority": req["priority"]
        })
    
    # Insert references
    for ref in references:
        conn.execute("""
        CREATE (r:ReferenceEntity {
            id: $id,
            standard: $standard,
            version: $version,
            section: $section,
            description: $description,
            level: 1
        })
        """, {
            "id": ref["id"],
            "standard": ref["standard"],
            "version": ref["version"],
            "section": ref["section"],
            "description": ref["description"]
        })
    
    # Create IMPLEMENTS relationships
    for req in requirements:
        for ref_id in req["references"]:
            conn.execute("""
            MATCH (req:RequirementEntity {uri: $uri}),
                  (ref:ReferenceEntity {id: $ref_id})
            CREATE (req)-[:IMPLEMENTS {status: 'verified'}]->(ref)
            """, {"uri": req["uri"], "ref_id": ref_id})
    
    print(f"Loaded {len(requirements)} requirements and {len(references)} references.\n")


def validate_mandatory_references(conn, config):
    """Run mandatory reference validation"""
    print("=== Mandatory Reference Validation Report ===\n")
    
    # Get all requirements with their references
    # First get all active requirements
    req_result = conn.execute("""
    MATCH (req:RequirementEntity)
    WHERE req.status = 'active'
    RETURN req.uri as uri, req.title as title, req.category as category, req.priority as priority
    ORDER BY req.category, req.uri
    """)
    
    requirements = []
    while req_result.has_next():
        row = req_result.get_next()
        requirements.append({
            "uri": row[0],
            "title": row[1],
            "category": row[2],
            "priority": row[3],
            "standards": [],
            "sections": []
        })
    
    # Then get their references
    for req in requirements:
        ref_result = conn.execute("""
        MATCH (req:RequirementEntity {uri: $uri})-[:IMPLEMENTS]->(ref:ReferenceEntity)
        RETURN DISTINCT ref.standard, ref.section
        """, {"uri": req["uri"]})
        
        while ref_result.has_next():
            ref_row = ref_result.get_next()
            req["standards"].append(ref_row[0])
            req["sections"].append(ref_row[1])
    
    violations = []
    warnings = []
    compliant = []
    
    print("Checking requirements by category:\n")
    
    current_category = None
    for req in requirements:
        uri = req["uri"]
        title = req["title"]
        category = req["category"]
        priority = req["priority"]
        standards = req["standards"]
        sections = req["sections"]
        
        # Print category header
        if category != current_category:
            if current_category:
                print()  # Add spacing between categories
            print(f"Category: {category}")
            print("-" * 50)
            current_category = category
        
        # Check for overrides
        override = config.check_override(uri, category)
        if override:
            print(f"  ✓ {uri}: {title}")
            print(f"    Override applied: {override.get('reason', 'Special rule')}")
            compliant.append(uri)
            continue
        
        # Get requirements for this category
        mandatory_standards = config.get_mandatory_standards(category)
        min_refs = config.get_minimum_references(category)
        
        # Check compliance
        issues = []
        
        # Check minimum reference count
        if len(standards) < min_refs:
            issues.append(f"Has {len(standards)} references, needs at least {min_refs}")
        
        # Check mandatory standards
        missing_standards = set(mandatory_standards) - set(standards)
        if missing_standards:
            issues.append(f"Missing required standards: {', '.join(sorted(missing_standards))}")
        
        # Check specific sections if category rules define them
        if category in config.rules["categories"] and "specific_sections" in config.rules["categories"][category]:
            for std in standards:
                if std in config.rules["categories"][category]["specific_sections"]:
                    required_sections = config.rules["categories"][category]["specific_sections"][std]
                    # Check if any section matches the required pattern
                    matching_sections = [s for s in sections if any(s.startswith(req) for req in required_sections)]
                    if not matching_sections and standards:
                        issues.append(f"{std} reference doesn't match required sections: {required_sections}")
        
        # Print requirement status
        if issues:
            print(f"  ✗ {uri}: {title}")
            print(f"    Current references: {', '.join(standards) if standards else 'None'}")
            for issue in issues:
                print(f"    Issue: {issue}")
            
            if priority in ["critical", "high"]:
                violations.append((uri, issues))
            else:
                warnings.append((uri, issues))
        else:
            print(f"  ✓ {uri}: {title}")
            print(f"    References: {', '.join(standards)}")
            compliant.append(uri)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total = len(compliant) + len(violations) + len(warnings)
    compliance_rate = len(compliant) / total if total > 0 else 0
    
    print(f"Total Requirements Checked: {total}")
    print(f"Compliant: {len(compliant)} ({len(compliant)/total*100:.1f}%)")
    print(f"Violations (High/Critical): {len(violations)} ({len(violations)/total*100:.1f}%)")
    print(f"Warnings (Medium/Low): {len(warnings)} ({len(warnings)/total*100:.1f}%)")
    print(f"Overall Compliance Rate: {compliance_rate:.1%}")
    
    threshold = config.rules["validation"]["coverage_threshold"]
    print(f"Required Threshold: {threshold:.1%}")
    print(f"Status: {'PASS' if compliance_rate >= threshold else 'FAIL'}")
    
    # Detailed violation report
    if violations:
        print("\n" + "=" * 60)
        print("CRITICAL VIOLATIONS (Must Fix)")
        print("=" * 60)
        for uri, issues in violations[:5]:  # Show first 5
            print(f"\n{uri}:")
            for issue in issues:
                print(f"  - {issue}")
        
        if len(violations) > 5:
            print(f"\n... and {len(violations) - 5} more violations")
    
    # Suggestions for fixing
    if violations or warnings:
        print("\n" + "=" * 60)
        print("SUGGESTED ACTIONS")
        print("=" * 60)
        print("\n1. Review mandatory standards for each category:")
        for cat in ["authentication", "authorization", "cryptography"]:
            stds = config.get_mandatory_standards(cat)
            print(f"   - {cat}: {', '.join(stds)}")
        
        print("\n2. For POC or experimental features, use appropriate URI patterns:")
        print("   - req:project:poc:* (exempt from mandatory references)")
        print("   - req:project:legacy:* (gradual compliance)")
        
        print("\n3. Configure overrides in mandatory_reference_rules.yaml for special cases")


def demonstrate_configuration():
    """Show how to use custom configuration"""
    print("\n" + "=" * 60)
    print("CONFIGURATION OPTIONS")
    print("=" * 60)
    
    print("\n1. Default Configuration:")
    print("   Uses built-in rules for standard categories")
    print("   config = MandatoryReferenceConfig()")
    
    print("\n2. Custom YAML Configuration:")
    print("   config = MandatoryReferenceConfig('data/mandatory_reference_rules.yaml')")
    
    print("\n3. Custom JSON Configuration:")
    print("   config = MandatoryReferenceConfig('data/custom_rules.json')")
    
    print("\n4. Key Configuration Options:")
    print("   - categories: Define mandatory standards per category")
    print("   - overrides: Pattern-based rules and exceptions")
    print("   - validation: Strict mode, thresholds, reporting")
    
    print("\n5. Override Examples:")
    print("   - POC Pattern: 'req:project:poc:*' → No mandatory references")
    print("   - Critical Pattern: 'req:project:critical:*' → Extra standards required")
    print("   - Temporary Exception: Expires after specified date")


def main():
    """Run the demonstration"""
    print("Mandatory Reference Validation Demo")
    print("==================================\n")
    
    # Setup database
    conn = setup_demo_database()
    
    # Load sample data
    load_sample_data(conn)
    
    # Create configuration (using default rules)
    config = MandatoryReferenceConfig()
    
    # You can also load custom configuration:
    # config = MandatoryReferenceConfig("data/mandatory_reference_rules.yaml")
    
    # Run validation
    validate_mandatory_references(conn, config)
    
    # Show configuration options
    demonstrate_configuration()
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()