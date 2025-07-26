"""
Test Mandatory References Module

Tests for enforcing category-based mandatory reference requirements.
Validates that requirements in specific categories have appropriate
references to standards (e.g., ASVS, NIST, ISO).
"""
import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Union, Any
from datetime import datetime
import kuzu


class MandatoryReferenceConfig:
    """Configuration for mandatory reference rules"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with configuration file or defaults"""
        self.rules = self._load_default_rules()
        
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                if config_file.suffix == '.yaml' or config_file.suffix == '.yml':
                    with open(config_file, 'r') as f:
                        custom_rules = yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    with open(config_file, 'r') as f:
                        custom_rules = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_file.suffix}")
                
                # Merge custom rules with defaults
                self._merge_rules(custom_rules)
    
    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default mandatory reference rules"""
        return {
            "categories": {
                "authentication": {
                    "mandatory_standards": ["ASVS", "NIST"],
                    "minimum_references": 2,
                    "specific_sections": {
                        "ASVS": ["V2", "V3"],  # Authentication and Session Management
                        "NIST": ["5.1", "5.2"]  # Authenticator and Verifier Requirements
                    }
                },
                "authorization": {
                    "mandatory_standards": ["ASVS", "ISO27001"],
                    "minimum_references": 2,
                    "specific_sections": {
                        "ASVS": ["V4"],  # Access Control
                        "ISO27001": ["A.9"]  # Access Control
                    }
                },
                "cryptography": {
                    "mandatory_standards": ["ASVS", "NIST", "FIPS"],
                    "minimum_references": 3,
                    "specific_sections": {
                        "ASVS": ["V6"],  # Stored Cryptography
                        "NIST": ["800-57", "800-175B"],
                        "FIPS": ["140-2", "140-3"]
                    }
                },
                "data_protection": {
                    "mandatory_standards": ["GDPR", "ISO27001", "ASVS"],
                    "minimum_references": 2,
                    "specific_sections": {
                        "GDPR": ["Article 32", "Article 25"],
                        "ISO27001": ["A.8", "A.12"],
                        "ASVS": ["V6", "V8"]
                    }
                },
                "logging": {
                    "mandatory_standards": ["ASVS", "ISO27001"],
                    "minimum_references": 1,
                    "specific_sections": {
                        "ASVS": ["V7"],  # Error Handling and Logging
                        "ISO27001": ["A.12.4"]
                    }
                },
                "api_security": {
                    "mandatory_standards": ["ASVS", "OWASP_API"],
                    "minimum_references": 2,
                    "specific_sections": {
                        "ASVS": ["V13"],  # API and Web Service
                        "OWASP_API": ["API1", "API2", "API3"]
                    }
                }
            },
            "overrides": {
                "patterns": [
                    {
                        "uri_pattern": "req:project:poc:*",
                        "rule": "relaxed",
                        "minimum_references": 0
                    },
                    {
                        "uri_pattern": "req:project:critical:*",
                        "rule": "strict",
                        "additional_standards": ["CC", "SOC2"]
                    }
                ],
                "exceptions": [
                    {
                        "uri": "req:project:legacy:auth:001",
                        "reason": "Legacy system - gradual compliance",
                        "temporary": True,
                        "expires": "2024-12-31"
                    }
                ]
            },
            "validation": {
                "strict_mode": False,  # If True, fail on missing references
                "warning_mode": True,   # If True, warn on missing references
                "coverage_threshold": 0.8,  # 80% of requirements must have references
                "report_format": "json"  # json, yaml, or markdown
            }
        }
    
    def _merge_rules(self, custom_rules: Dict[str, Any]):
        """Merge custom rules with defaults"""
        if "categories" in custom_rules:
            for category, rules in custom_rules["categories"].items():
                if category in self.rules["categories"]:
                    self.rules["categories"][category].update(rules)
                else:
                    self.rules["categories"][category] = rules
        
        if "overrides" in custom_rules:
            self.rules["overrides"].update(custom_rules["overrides"])
        
        if "validation" in custom_rules:
            self.rules["validation"].update(custom_rules["validation"])
    
    def get_mandatory_standards(self, category: str) -> List[str]:
        """Get mandatory standards for a category"""
        if category in self.rules["categories"]:
            return self.rules["categories"][category].get("mandatory_standards", [])
        return []
    
    def get_minimum_references(self, category: str) -> int:
        """Get minimum number of references required for a category"""
        if category in self.rules["categories"]:
            return self.rules["categories"][category].get("minimum_references", 1)
        return 1
    
    def check_override(self, uri: str, category: str) -> Optional[Dict[str, Any]]:
        """Check if URI has override rules"""
        # Check patterns
        for pattern_rule in self.rules["overrides"]["patterns"]:
            pattern = pattern_rule["uri_pattern"]
            if self._matches_pattern(uri, pattern):
                return pattern_rule
        
        # Check exceptions
        for exception in self.rules["overrides"]["exceptions"]:
            if exception["uri"] == uri:
                # Check if temporary exception is still valid
                if exception.get("temporary") and "expires" in exception:
                    expiry_date = datetime.strptime(exception["expires"], "%Y-%m-%d")
                    if datetime.now() > expiry_date:
                        continue  # Exception has expired
                return exception
        
        return None
    
    def _matches_pattern(self, uri: str, pattern: str) -> bool:
        """Check if URI matches pattern (supports * wildcard)"""
        import re
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", uri))


class TestMandatoryReferences:
    """Test mandatory reference requirements"""
    
    @pytest.fixture
    def config(self):
        """Create configuration instance"""
        return MandatoryReferenceConfig()
    
    @pytest.fixture
    def db_with_data(self, tmp_path):
        """Create database with test data"""
        db_path = tmp_path / "test.db"
        db = kuzu.Database(str(db_path))
        conn = kuzu.Connection(db)
        
        # Create schema
        conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING,
            category STRING,
            priority STRING,
            status STRING DEFAULT 'draft'
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
        
        # Insert test requirements
        test_requirements = [
            # Authentication requirements
            ("req:auth:001", "User Login", "Basic user authentication", "authentication", "high"),
            ("req:auth:002", "MFA Support", "Multi-factor authentication", "authentication", "high"),
            ("req:auth:003", "Password Policy", "Enforce strong passwords", "authentication", "medium"),
            
            # Authorization requirements
            ("req:authz:001", "Role-Based Access", "RBAC implementation", "authorization", "high"),
            ("req:authz:002", "Permission Check", "Fine-grained permissions", "authorization", "medium"),
            
            # Cryptography requirements
            ("req:crypto:001", "Data Encryption", "AES-256 encryption", "cryptography", "critical"),
            ("req:crypto:002", "Key Management", "Secure key storage", "cryptography", "critical"),
            
            # Data protection requirements
            ("req:data:001", "PII Protection", "Protect personal data", "data_protection", "high"),
            ("req:data:002", "Data Retention", "GDPR compliant retention", "data_protection", "high"),
            
            # POC requirements (should be exempt)
            ("req:project:poc:001", "Prototype Feature", "Quick prototype", "authentication", "low"),
        ]
        
        for uri, title, desc, category, priority in test_requirements:
            conn.execute("""
            CREATE (r:RequirementEntity {
                uri: $uri,
                title: $title,
                description: $description,
                category: $category,
                priority: $priority
            })
            """, {"uri": uri, "title": title, "description": desc, "category": category, "priority": priority})
        
        # Insert test references
        test_references = [
            ("ASVS_V2.1.1", "OWASP ASVS", "4.0.3", "V2.1", "Password length requirement", 1),
            ("ASVS_V2.1.2", "OWASP ASVS", "4.0.3", "V2.1", "Password complexity", 1),
            ("ASVS_V4.1.1", "OWASP ASVS", "4.0.3", "V4.1", "Access control verification", 1),
            ("NIST_5.1.1", "NIST 800-63B", "3", "5.1", "Authentication requirements", 2),
            ("ISO_A9.1", "ISO27001", "2022", "A.9", "Access control policy", 2),
            ("GDPR_Art32", "GDPR", "2018", "Article 32", "Security of processing", 3),
        ]
        
        for ref_id, standard, version, section, desc, level in test_references:
            conn.execute("""
            CREATE (r:ReferenceEntity {
                id: $id,
                standard: $standard,
                version: $version,
                section: $section,
                description: $description,
                level: $level
            })
            """, {"id": ref_id, "standard": standard, "version": version, 
                  "section": section, "description": desc, "level": level})
        
        # Create some IMPLEMENTS relationships
        implements_rels = [
            ("req:auth:001", "ASVS_V2.1.1", "implemented"),
            ("req:auth:001", "NIST_5.1.1", "implemented"),
            ("req:auth:002", "ASVS_V2.1.2", "planned"),
            ("req:authz:001", "ASVS_V4.1.1", "implemented"),
            ("req:data:001", "GDPR_Art32", "implemented"),
        ]
        
        for req_uri, ref_id, status in implements_rels:
            conn.execute("""
            MATCH (req:RequirementEntity {uri: $req_uri}),
                  (ref:ReferenceEntity {id: $ref_id})
            CREATE (req)-[:IMPLEMENTS {status: $status}]->(ref)
            """, {"req_uri": req_uri, "ref_id": ref_id, "status": status})
        
        return conn
    
    def test_validate_mandatory_references(self, db_with_data, config):
        """Test validation of mandatory references by category"""
        conn = db_with_data
        
        # Get all requirements with their references
        # First get all requirements
        req_result = conn.execute("""
        MATCH (req:RequirementEntity)
        RETURN req.uri as uri, req.category as category
        ORDER BY req.uri
        """)
        
        requirements = []
        while req_result.has_next():
            row = req_result.get_next()
            requirements.append({
                "uri": row[0],
                "category": row[1],
                "standards": []
            })
        
        # Then get their references
        for req in requirements:
            ref_result = conn.execute("""
            MATCH (req:RequirementEntity {uri: $uri})-[:IMPLEMENTS]->(ref:ReferenceEntity)
            RETURN DISTINCT ref.standard
            """, {"uri": req["uri"]})
            
            while ref_result.has_next():
                req["standards"].append(ref_result.get_next()[0])
        
        violations = []
        warnings = []
        
        for req in requirements:
            uri = req["uri"]
            category = req["category"]
            standards = req["standards"]
            
            # Check for overrides
            override = config.check_override(uri, category)
            if override and override.get("rule") == "relaxed":
                continue  # Skip validation for relaxed rules
            
            # Get mandatory standards for this category
            mandatory = config.get_mandatory_standards(category)
            min_refs = config.get_minimum_references(category)
            
            # Check minimum number of references
            if len(standards) < min_refs:
                msg = f"{uri} ({category}) has {len(standards)} references, needs {min_refs}"
                if config.rules["validation"]["strict_mode"]:
                    violations.append(msg)
                else:
                    warnings.append(msg)
            
            # Check mandatory standards
            missing_standards = set(mandatory) - set(standards)
            if missing_standards:
                msg = f"{uri} ({category}) missing required standards: {missing_standards}"
                if config.rules["validation"]["strict_mode"]:
                    violations.append(msg)
                else:
                    warnings.append(msg)
        
        # Print report
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if violations:
            print("\nViolations:")
            for violation in violations:
                print(f"  - {violation}")
        
        # In strict mode, fail if there are violations
        if config.rules["validation"]["strict_mode"]:
            assert len(violations) == 0, f"Found {len(violations)} violations"
        
        # Always check that we found some issues (for test validation)
        assert len(warnings) > 0 or len(violations) > 0
    
    def test_coverage_validation(self, db_with_data, config):
        """Test overall coverage of references"""
        conn = db_with_data
        
        # Get coverage statistics
        total_result = conn.execute("""
        MATCH (req:RequirementEntity)
        RETURN count(req) as total
        """)
        total_reqs = total_result.get_next()[0]
        
        with_refs_result = conn.execute("""
        MATCH (req:RequirementEntity)
        WHERE EXISTS {
            MATCH (req)-[:IMPLEMENTS]->(:ReferenceEntity)
        }
        RETURN count(req) as with_refs
        """)
        reqs_with_refs = with_refs_result.get_next()[0]
        
        coverage = reqs_with_refs / total_reqs if total_reqs > 0 else 0
        threshold = config.rules["validation"]["coverage_threshold"]
        
        print(f"\nCoverage Report:")
        print(f"  Total requirements: {total_reqs}")
        print(f"  Requirements with references: {reqs_with_refs}")
        print(f"  Coverage: {coverage:.1%}")
        print(f"  Threshold: {threshold:.1%}")
        
        if coverage < threshold:
            msg = f"Coverage {coverage:.1%} is below threshold {threshold:.1%}"
            if config.rules["validation"]["strict_mode"]:
                pytest.fail(msg)
            else:
                print(f"  WARNING: {msg}")
    
    def test_category_specific_rules(self, db_with_data, config):
        """Test category-specific section requirements"""
        conn = db_with_data
        
        # Check authentication requirements have proper ASVS sections
        auth_reqs = conn.execute("""
        MATCH (req:RequirementEntity {category: 'authentication'})
        RETURN req.uri as uri
        """)
        
        auth_requirements = []
        while auth_reqs.has_next():
            row = auth_reqs.get_next()
            uri = row[0]
            
            # Get ASVS sections for this requirement
            section_result = conn.execute("""
            MATCH (req:RequirementEntity {uri: $uri})-[:IMPLEMENTS]->(ref:ReferenceEntity)
            WHERE ref.standard = 'OWASP ASVS'
            RETURN ref.section
            """, {"uri": uri})
            
            sections = []
            while section_result.has_next():
                sections.append(section_result.get_next()[0])
            
            auth_requirements.append((uri, sections))
        
        auth_section_violations = []
        required_sections = config.rules["categories"]["authentication"]["specific_sections"]["ASVS"]
        
        for uri, sections in auth_requirements:
            
            # Check if any required section is referenced
            has_required = any(
                any(section.startswith(req_sec) for section in sections)
                for req_sec in required_sections
            )
            
            if not has_required and sections:  # Has ASVS refs but wrong sections
                auth_section_violations.append(
                    f"{uri} references ASVS but not required sections {required_sections}"
                )
        
        if auth_section_violations:
            print("\nSection-specific violations:")
            for violation in auth_section_violations:
                print(f"  - {violation}")
    
    def test_load_custom_config(self, tmp_path):
        """Test loading custom configuration from YAML"""
        # Create custom config
        custom_config = {
            "categories": {
                "authentication": {
                    "mandatory_standards": ["ASVS", "NIST", "ISO27001"],
                    "minimum_references": 3
                },
                "custom_category": {
                    "mandatory_standards": ["CUSTOM_STD"],
                    "minimum_references": 1
                }
            },
            "validation": {
                "strict_mode": True,
                "coverage_threshold": 0.95
            }
        }
        
        config_file = tmp_path / "custom_rules.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(custom_config, f)
        
        # Load config
        config = MandatoryReferenceConfig(str(config_file))
        
        # Verify merged rules
        assert "ISO27001" in config.get_mandatory_standards("authentication")
        assert config.get_minimum_references("authentication") == 3
        assert "custom_category" in config.rules["categories"]
        assert config.rules["validation"]["coverage_threshold"] == 0.95
    
    def test_override_patterns(self, config):
        """Test URI pattern matching for overrides"""
        # Test POC pattern
        assert config.check_override("req:project:poc:test", "authentication") is not None
        assert config.check_override("req:project:poc:feature:001", "any") is not None
        
        # Test critical pattern  
        critical_override = config.check_override("req:project:critical:security:001", "any")
        assert critical_override is not None
        assert "additional_standards" in critical_override
        
        # Test non-matching pattern
        assert config.check_override("req:normal:001", "authentication") is None
    
    def test_temporary_exceptions(self, config):
        """Test temporary exception handling"""
        # Add a current exception
        current_exception = {
            "uri": "req:temp:001",
            "reason": "Migration in progress",
            "temporary": True,
            "expires": "2025-12-31"
        }
        config.rules["overrides"]["exceptions"].append(current_exception)
        
        # Add an expired exception
        expired_exception = {
            "uri": "req:temp:002", 
            "reason": "Old exception",
            "temporary": True,
            "expires": "2020-12-31"
        }
        config.rules["overrides"]["exceptions"].append(expired_exception)
        
        # Current exception should be found
        assert config.check_override("req:temp:001", "any") is not None
        
        # Expired exception should not be found
        assert config.check_override("req:temp:002", "any") is None
    
    def test_generate_compliance_report(self, db_with_data, config):
        """Test generating a compliance report"""
        conn = db_with_data
        
        # Collect all compliance data
        # First get all requirements
        req_result = conn.execute("""
        MATCH (req:RequirementEntity)
        RETURN req.uri as uri, req.category as category, req.priority as priority
        ORDER BY req.category, req.uri
        """)
        
        all_requirements = []
        while req_result.has_next():
            row = req_result.get_next()
            all_requirements.append({
                "uri": row[0],
                "category": row[1],
                "priority": row[2],
                "references": []
            })
        
        # Then get their references
        for req in all_requirements:
            ref_result = conn.execute("""
            MATCH (req:RequirementEntity {uri: $uri})-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            RETURN ref.standard, ref.section, impl.status
            """, {"uri": req["uri"]})
            
            while ref_result.has_next():
                ref_row = ref_result.get_next()
                req["references"].append({
                    "standard": ref_row[0],
                    "section": ref_row[1],
                    "status": ref_row[2]
                })
        
        report = {
            "summary": {
                "total_requirements": 0,
                "compliant": 0,
                "non_compliant": 0,
                "warnings": 0
            },
            "by_category": {},
            "violations": [],
            "warnings": []
        }
        
        for req in all_requirements:
            uri = req["uri"]
            category = req["category"]
            priority = req["priority"]
            references = req["references"]
            
            report["summary"]["total_requirements"] += 1
            
            # Initialize category if needed
            if category not in report["by_category"]:
                report["by_category"][category] = {
                    "total": 0,
                    "compliant": 0,
                    "requirements": []
                }
            
            report["by_category"][category]["total"] += 1
            
            # Check compliance
            override = config.check_override(uri, category)
            is_compliant = True
            issues = []
            
            if not override or override.get("rule") != "relaxed":
                mandatory = config.get_mandatory_standards(category)
                min_refs = config.get_minimum_references(category)
                
                ref_standards = [r["standard"] for r in references]
                
                if len(ref_standards) < min_refs:
                    is_compliant = False
                    issues.append(f"Only {len(ref_standards)} references, needs {min_refs}")
                
                missing = set(mandatory) - set(ref_standards)
                if missing:
                    is_compliant = False
                    issues.append(f"Missing standards: {', '.join(missing)}")
            
            if is_compliant:
                report["summary"]["compliant"] += 1
                report["by_category"][category]["compliant"] += 1
            else:
                if priority in ["critical", "high"]:
                    report["summary"]["non_compliant"] += 1
                    report["violations"].extend([f"{uri}: {issue}" for issue in issues])
                else:
                    report["summary"]["warnings"] += 1
                    report["warnings"].extend([f"{uri}: {issue}" for issue in issues])
            
            report["by_category"][category]["requirements"].append({
                "uri": uri,
                "compliant": is_compliant,
                "references": len(references),
                "issues": issues
            })
        
        # Calculate percentages
        total = report["summary"]["total_requirements"]
        if total > 0:
            report["summary"]["compliance_rate"] = report["summary"]["compliant"] / total
        
        # Output report
        print("\n=== Mandatory Reference Compliance Report ===")
        print(f"\nSummary:")
        print(f"  Total Requirements: {report['summary']['total_requirements']}")
        print(f"  Compliant: {report['summary']['compliant']}")
        print(f"  Non-Compliant: {report['summary']['non_compliant']}")
        print(f"  Warnings: {report['summary']['warnings']}")
        if "compliance_rate" in report["summary"]:
            print(f"  Compliance Rate: {report['summary']['compliance_rate']:.1%}")
        
        print(f"\nBy Category:")
        for cat, data in report["by_category"].items():
            rate = data["compliant"] / data["total"] if data["total"] > 0 else 0
            print(f"  {cat}: {data['compliant']}/{data['total']} ({rate:.1%})")
        
        if report["violations"]:
            print(f"\nCritical Violations ({len(report['violations'])}):")
            for v in report["violations"][:5]:  # Show first 5
                print(f"  - {v}")
            if len(report["violations"]) > 5:
                print(f"  ... and {len(report['violations']) - 5} more")
        
        # Verify report was generated correctly
        assert "summary" in report
        assert "by_category" in report
        assert report["summary"]["total_requirements"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])