"""
Compliance Mapping Tests (IMPLEMENTS Relationship)

Tests for mapping RequirementEntity to ReferenceEntity
and tracking compliance status
"""
import pytest
import kuzu
import tempfile
import shutil
from datetime import datetime


class TestComplianceMapping:
    """Test IMPLEMENTS relationship between RequirementEntity and ReferenceEntity"""

    @pytest.fixture
    def db_with_schema(self, tmp_path):
        """Create database with full schema"""
        db = kuzu.Database(str(tmp_path))
        conn = kuzu.Connection(db)
        
        # Create RequirementEntity table
        conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING,
            category STRING,
            created_date STRING
        )
        """)
        
        # Create ReferenceEntity table
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
        
        # Create IMPLEMENTS relationship
        conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM RequirementEntity TO ReferenceEntity,
            status STRING,
            justification STRING,
            verified_date STRING,
            evidence_uri STRING
        )
        """)
        
        # Insert sample data
        # Requirements
        requirements = [
            ('req://auth/password-policy', 'Password Policy', 'Password must be at least 12 characters', 'authentication', '2024-01-01'),
            ('req://auth/account-lockout', 'Account Lockout', 'Lock account after 5 failed attempts', 'authentication', '2024-01-02'),
            ('req://session/token-generation', 'Session Token', 'Generate new token on login', 'session', '2024-01-03'),
            ('req://crypto/secure-random', 'Secure Random', 'Use cryptographically secure random', 'cryptography', '2024-01-04'),
        ]
        
        for req in requirements:
            conn.execute(f"""
                CREATE (r:RequirementEntity {{
                    uri: '{req[0]}',
                    title: '{req[1]}',
                    description: '{req[2]}',
                    category: '{req[3]}',
                    created_date: '{req[4]}'
                }})
            """)
        
        # References (ASVS)
        references = [
            ('ASVS-V2.1.1', 'ASVS', '4.0.3', 'V2.1.1', 'Verify that user set passwords are at least 12 characters in length', 1, 'authentication'),
            ('ASVS-V2.1.7', 'ASVS', '4.0.3', 'V2.1.7', 'Verify that passwords submitted are checked against commonly used passwords', 2, 'authentication'),
            ('ASVS-V2.2.1', 'ASVS', '4.0.3', 'V2.2.1', 'Verify that anti-automation controls are effective', 1, 'authentication'),
            ('ASVS-V3.2.1', 'ASVS', '4.0.3', 'V3.2.1', 'Verify the application generates a new session token on user authentication', 1, 'session'),
            ('ASVS-V6.3.1', 'ASVS', '4.0.3', 'V6.3.1', 'Verify that all random numbers are created using approved cryptographically secure random number generator', 1, 'cryptography'),
        ]
        
        for ref in references:
            conn.execute(f"""
                CREATE (r:ReferenceEntity {{
                    id: '{ref[0]}',
                    standard: '{ref[1]}',
                    version: '{ref[2]}',
                    section: '{ref[3]}',
                    description: '{ref[4]}',
                    level: {ref[5]},
                    category: '{ref[6]}'
                }})
            """)
        
        yield conn
        conn.close()

    def test_create_implements_relationship(self, db_with_schema):
        """IMPLEMENTS関係の作成が正しく動作すること"""
        # Create relationship between password policy and ASVS V2.1.1
        db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://auth/password-policy'}),
                  (ref:ReferenceEntity {id: 'ASVS-V2.1.1'})
            CREATE (req)-[impl:IMPLEMENTS {
                status: 'completed',
                justification: 'Password length validation implemented',
                verified_date: '2024-01-15',
                evidence_uri: 'req://test/auth/test_password_length'
            }]->(ref)
        """)
        
        # Verify relationship exists
        result = db_with_schema.execute("""
            MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            WHERE req.uri = 'req://auth/password-policy'
            RETURN req.uri, ref.id, impl.status
        """).get_as_df()
        
        assert len(result) == 1
        assert result.iloc[0]['ref.id'] == 'ASVS-V2.1.1'
        assert result.iloc[0]['impl.status'] == 'completed'

    def test_multiple_implements_relationships(self, db_with_schema):
        """1つの要件が複数の参照要件を実装できること"""
        # Password policy implements multiple ASVS requirements
        mappings = [
            ('ASVS-V2.1.1', 'completed', 'Length check implemented'),
            ('ASVS-V2.1.7', 'partial', 'Basic common password check, needs expansion')
        ]
        
        for ref_id, status, justification in mappings:
            db_with_schema.execute(f"""
                MATCH (req:RequirementEntity {{uri: 'req://auth/password-policy'}}),
                      (ref:ReferenceEntity {{id: '{ref_id}'}})
                CREATE (req)-[impl:IMPLEMENTS {{
                    status: '{status}',
                    justification: '{justification}',
                    verified_date: '2024-01-15',
                    evidence_uri: 'req://test/auth/password_tests'
                }}]->(ref)
            """)
        
        # Verify both relationships
        result = db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://auth/password-policy'})-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            RETURN ref.id, impl.status
            ORDER BY ref.id
        """).get_as_df()
        
        assert len(result) == 2
        assert result.iloc[0]['impl.status'] == 'completed'
        assert result.iloc[1]['impl.status'] == 'partial'

    def test_compliance_status_types(self, db_with_schema):
        """各種コンプライアンスステータスが正しく記録されること"""
        # Create relationships with different statuses
        status_mappings = [
            ('req://auth/password-policy', 'ASVS-V2.1.1', 'completed', 'Fully implemented and tested'),
            ('req://auth/account-lockout', 'ASVS-V2.2.1', 'partial', 'Basic implementation, needs rate limiting'),
            ('req://session/token-generation', 'ASVS-V3.2.1', 'planned', 'Scheduled for Q2 2024'),
            ('req://crypto/secure-random', 'ASVS-V6.3.1', 'not_applicable', 'Using platform CSPRNG')
        ]
        
        for req_uri, ref_id, status, justification in status_mappings:
            db_with_schema.execute(f"""
                MATCH (req:RequirementEntity {{uri: '{req_uri}'}}),
                      (ref:ReferenceEntity {{id: '{ref_id}'}})
                CREATE (req)-[impl:IMPLEMENTS {{
                    status: '{status}',
                    justification: '{justification}',
                    verified_date: '2024-01-20',
                    evidence_uri: 'req://evidence/{req_uri.split("/")[-1]}'
                }}]->(ref)
            """)
        
        # Verify status distribution
        result = db_with_schema.execute("""
            MATCH ()-[impl:IMPLEMENTS]->()
            RETURN impl.status as status, count(*) as count
            ORDER BY status
        """).get_as_df()
        
        expected_statuses = {
            'completed': 1,
            'not_applicable': 1,
            'partial': 1,
            'planned': 1
        }
        
        for _, row in result.iterrows():
            assert expected_statuses[row['status']] == row['count']

    def test_find_unmapped_requirements(self, db_with_schema):
        """マッピングされていない要件の検出が正しく動作すること"""
        # Create one mapping
        db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://auth/password-policy'}),
                  (ref:ReferenceEntity {id: 'ASVS-V2.1.1'})
            CREATE (req)-[impl:IMPLEMENTS {status: 'completed'}]->(ref)
        """)
        
        # Find requirements without any mappings
        result = db_with_schema.execute("""
            MATCH (req:RequirementEntity)
            WHERE NOT EXISTS {
                MATCH (req)-[:IMPLEMENTS]->(:ReferenceEntity)
            }
            RETURN req.uri, req.title
            ORDER BY req.uri
        """).get_as_df()
        
        assert len(result) == 3  # 4 requirements - 1 mapped = 3 unmapped
        unmapped_uris = result['req.uri'].tolist()
        assert 'req://auth/password-policy' not in unmapped_uris

    def test_find_unimplemented_references(self, db_with_schema):
        """実装されていない参照要件の検出が正しく動作すること"""
        # Create some mappings
        db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://auth/password-policy'}),
                  (ref:ReferenceEntity {id: 'ASVS-V2.1.1'})
            CREATE (req)-[:IMPLEMENTS {status: 'completed'}]->(ref)
        """)
        
        db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://session/token-generation'}),
                  (ref:ReferenceEntity {id: 'ASVS-V3.2.1'})
            CREATE (req)-[:IMPLEMENTS {status: 'planned'}]->(ref)
        """)
        
        # Find reference requirements not implemented by any requirement
        result = db_with_schema.execute("""
            MATCH (ref:ReferenceEntity)
            WHERE NOT EXISTS {
                MATCH (:RequirementEntity)-[:IMPLEMENTS]->(ref)
            }
            RETURN ref.id, ref.section, ref.category
            ORDER BY ref.id
        """).get_as_df()
        
        assert len(result) == 3  # 5 references - 2 mapped = 3
        unimplemented_ids = result['ref.id'].tolist()
        assert 'ASVS-V2.1.7' in unimplemented_ids
        assert 'ASVS-V2.2.1' in unimplemented_ids
        assert 'ASVS-V6.3.1' in unimplemented_ids

    def test_compliance_by_category(self, db_with_schema):
        """カテゴリ別のコンプライアンス状況が正しく取得できること"""
        # Create various mappings
        mappings = [
            ('req://auth/password-policy', 'ASVS-V2.1.1', 'completed'),
            ('req://auth/account-lockout', 'ASVS-V2.2.1', 'partial'),
            ('req://session/token-generation', 'ASVS-V3.2.1', 'completed'),
        ]
        
        for req_uri, ref_id, status in mappings:
            db_with_schema.execute(f"""
                MATCH (req:RequirementEntity {{uri: '{req_uri}'}}),
                      (ref:ReferenceEntity {{id: '{ref_id}'}})
                CREATE (req)-[:IMPLEMENTS {{status: '{status}'}}]->(ref)
            """)
        
        # Get compliance by category
        result = db_with_schema.execute("""
            MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            RETURN ref.category as category, 
                   impl.status as status,
                   count(*) as count
            ORDER BY category, status
        """).get_as_df()
        
        # Verify results
        auth_results = result[result['category'] == 'authentication']
        assert len(auth_results) == 2  # completed and partial
        
        session_results = result[result['category'] == 'session']
        assert len(session_results) == 1
        assert session_results.iloc[0]['status'] == 'completed'

    def test_update_compliance_status(self, db_with_schema):
        """コンプライアンスステータスの更新が正しく動作すること"""
        # Create initial mapping
        db_with_schema.execute("""
            MATCH (req:RequirementEntity {uri: 'req://auth/password-policy'}),
                  (ref:ReferenceEntity {id: 'ASVS-V2.1.1'})
            CREATE (req)-[impl:IMPLEMENTS {
                status: 'planned',
                justification: 'Initial planning',
                verified_date: '2024-01-01'
            }]->(ref)
        """)
        
        # Update status to completed
        db_with_schema.execute("""
            MATCH (:RequirementEntity {uri: 'req://auth/password-policy'})-[impl:IMPLEMENTS]->(:ReferenceEntity {id: 'ASVS-V2.1.1'})
            SET impl.status = 'completed',
                impl.justification = 'Implementation complete and tested',
                impl.verified_date = '2024-02-01',
                impl.evidence_uri = 'req://test/auth/password_validation'
        """)
        
        # Verify update
        result = db_with_schema.execute("""
            MATCH (:RequirementEntity {uri: 'req://auth/password-policy'})-[impl:IMPLEMENTS]->(:ReferenceEntity {id: 'ASVS-V2.1.1'})
            RETURN impl.*
        """).get_as_df()
        
        assert result.iloc[0]['impl.status'] == 'completed'
        assert result.iloc[0]['impl.verified_date'] == '2024-02-01'
        assert 'password_validation' in result.iloc[0]['impl.evidence_uri']