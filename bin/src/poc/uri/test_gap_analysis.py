"""
Gap Analysis Tests

Tests for analyzing compliance gaps and coverage
between RequirementEntity and ReferenceEntity
"""
import pytest
import kuzu
import tempfile
import shutil


class TestGapAnalysis:
    """Test gap analysis functionality for compliance tracking"""

    @pytest.fixture
    def db_with_comprehensive_data(self, tmp_path):
        """Create database with comprehensive test data"""
        db = kuzu.Database(str(tmp_path))
        conn = kuzu.Connection(db)
        
        # Create schema
        conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING,
            category STRING,
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
            status STRING,
            justification STRING,
            verified_date STRING,
            evidence_uri STRING
        )
        """)
        
        # Insert comprehensive ASVS data (Level 1 and 2)
        asvs_references = [
            # Authentication - V2.1 (Password Security)
            ('ASVS-V2.1.1', 'ASVS', '4.0.3', 'V2.1.1', 'Verify that user set passwords are at least 12 characters', 1, 'authentication'),
            ('ASVS-V2.1.2', 'ASVS', '4.0.3', 'V2.1.2', 'Verify that passwords can contain spaces', 1, 'authentication'),
            ('ASVS-V2.1.3', 'ASVS', '4.0.3', 'V2.1.3', 'Verify that password truncation is not performed', 1, 'authentication'),
            ('ASVS-V2.1.7', 'ASVS', '4.0.3', 'V2.1.7', 'Verify passwords are checked against common passwords', 2, 'authentication'),
            
            # Authentication - V2.2 (General Authenticator)
            ('ASVS-V2.2.1', 'ASVS', '4.0.3', 'V2.2.1', 'Verify that anti-automation controls are effective', 1, 'authentication'),
            ('ASVS-V2.2.2', 'ASVS', '4.0.3', 'V2.2.2', 'Verify that anti-automation includes account lockout', 1, 'authentication'),
            
            # Session Management - V3.2
            ('ASVS-V3.2.1', 'ASVS', '4.0.3', 'V3.2.1', 'Verify new session token on authentication', 1, 'session'),
            ('ASVS-V3.2.2', 'ASVS', '4.0.3', 'V3.2.2', 'Verify session tokens possess 64 bits of entropy', 1, 'session'),
            ('ASVS-V3.2.3', 'ASVS', '4.0.3', 'V3.2.3', 'Verify session tokens are stored securely', 2, 'session'),
            
            # Access Control - V4.1
            ('ASVS-V4.1.1', 'ASVS', '4.0.3', 'V4.1.1', 'Verify access control rules are enforced', 1, 'access_control'),
            ('ASVS-V4.1.2', 'ASVS', '4.0.3', 'V4.1.2', 'Verify access control attributes are protected', 2, 'access_control'),
            ('ASVS-V4.1.3', 'ASVS', '4.0.3', 'V4.1.3', 'Verify least privilege principle', 1, 'access_control'),
        ]
        
        for ref in asvs_references:
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
        
        # Insert project requirements
        requirements = [
            ('req://auth/password-policy', 'Password Policy', 'Enforce strong passwords', 'authentication'),
            ('req://auth/password-validation', 'Password Validation', 'Validate password complexity', 'authentication'),
            ('req://auth/rate-limiting', 'Rate Limiting', 'Prevent brute force attacks', 'authentication'),
            ('req://session/token-management', 'Token Management', 'Secure session token handling', 'session'),
            ('req://access/rbac', 'Role-Based Access', 'Implement RBAC', 'access_control'),
        ]
        
        for req in requirements:
            conn.execute(f"""
                CREATE (r:RequirementEntity {{
                    uri: '{req[0]}',
                    title: '{req[1]}',
                    description: '{req[2]}',
                    category: '{req[3]}',
                    created_date: '2024-01-01'
                }})
            """)
        
        # Create compliance mappings
        mappings = [
            # Password policy implements multiple ASVS requirements
            ('req://auth/password-policy', 'ASVS-V2.1.1', 'completed'),
            ('req://auth/password-policy', 'ASVS-V2.1.2', 'completed'),
            ('req://auth/password-validation', 'ASVS-V2.1.7', 'partial'),
            
            # Rate limiting implements anti-automation
            ('req://auth/rate-limiting', 'ASVS-V2.2.1', 'completed'),
            
            # Session management
            ('req://session/token-management', 'ASVS-V3.2.1', 'completed'),
            ('req://session/token-management', 'ASVS-V3.2.2', 'planned'),
            
            # Access control
            ('req://access/rbac', 'ASVS-V4.1.1', 'completed'),
        ]
        
        for req_uri, ref_id, status in mappings:
            conn.execute(f"""
                MATCH (req:RequirementEntity {{uri: '{req_uri}'}}),
                      (ref:ReferenceEntity {{id: '{ref_id}'}})
                CREATE (req)-[:IMPLEMENTS {{
                    status: '{status}',
                    verified_date: '2024-01-15'
                }}]->(ref)
            """)
        
        yield conn
        conn.close()

    def test_calculate_overall_coverage(self, db_with_comprehensive_data):
        """全体のカバレッジ計算が正しく動作すること"""
        # Calculate overall coverage
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            OPTIONAL MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref)
            WITH ref, impl
            RETURN 
                count(DISTINCT ref) as total_references,
                count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) as covered_references,
                CAST(count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) AS DOUBLE) / 
                CAST(count(DISTINCT ref) AS DOUBLE) * 100 as coverage_percentage
        """).get_as_df()
        
        assert result.iloc[0]['total_references'] == 12
        assert result.iloc[0]['covered_references'] == 7
        assert result.iloc[0]['coverage_percentage'] == pytest.approx(58.33, rel=0.01)

    def test_coverage_by_level(self, db_with_comprehensive_data):
        """レベル別のカバレッジ計算が正しく動作すること"""
        # Calculate coverage by ASVS level
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            OPTIONAL MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref)
            WITH ref.level as level, ref, impl
            RETURN 
                level,
                count(DISTINCT ref) as total,
                count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) as covered,
                CAST(count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) AS DOUBLE) / 
                CAST(count(DISTINCT ref) AS DOUBLE) * 100 as percentage
            ORDER BY level
        """).get_as_df()
        
        # Level 1 coverage
        level1 = result[result['level'] == 1].iloc[0]
        assert level1['total'] == 8
        assert level1['covered'] == 5
        assert level1['percentage'] == 62.5
        
        # Level 2 coverage
        level2 = result[result['level'] == 2].iloc[0]
        assert level2['total'] == 4
        assert level2['covered'] == 2
        assert level2['percentage'] == 50.0

    def test_coverage_by_category(self, db_with_comprehensive_data):
        """カテゴリ別のカバレッジ計算が正しく動作すること"""
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            OPTIONAL MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref)
            WITH ref.category as category, ref, impl
            RETURN 
                category,
                count(DISTINCT ref) as total,
                count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) as covered,
                CAST(count(DISTINCT CASE WHEN impl IS NOT NULL THEN ref END) AS DOUBLE) / 
                CAST(count(DISTINCT ref) AS DOUBLE) * 100 as percentage
            ORDER BY category
        """).get_as_df()
        
        # Check authentication coverage
        auth_coverage = result[result['category'] == 'authentication'].iloc[0]
        assert auth_coverage['total'] == 6
        assert auth_coverage['covered'] == 4
        assert auth_coverage['percentage'] == pytest.approx(66.67, rel=0.01)

    def test_gap_identification(self, db_with_comprehensive_data):
        """ギャップ（未実装の参照要件）の特定が正しく動作すること"""
        # Find uncovered references
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            WHERE NOT EXISTS {
                MATCH (:RequirementEntity)-[:IMPLEMENTS]->(ref)
            }
            RETURN ref.id, ref.section, ref.level, ref.category, ref.description
            ORDER BY ref.level, ref.section
        """).get_as_df()
        
        assert len(result) == 5
        
        # Verify specific gaps
        gap_ids = result['ref.id'].tolist()
        assert 'ASVS-V2.1.3' in gap_ids  # Password truncation
        assert 'ASVS-V2.2.2' in gap_ids  # Account lockout
        assert 'ASVS-V3.2.3' in gap_ids  # Secure token storage
        assert 'ASVS-V4.1.2' in gap_ids  # Protected attributes
        assert 'ASVS-V4.1.3' in gap_ids  # Least privilege

    def test_compliance_status_breakdown(self, db_with_comprehensive_data):
        """コンプライアンスステータスの内訳が正しく取得できること"""
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            OPTIONAL MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref)
            WITH ref, impl.status as status
            RETURN 
                CASE 
                    WHEN status IS NULL THEN 'not_implemented'
                    ELSE status
                END as compliance_status,
                count(*) as count
            ORDER BY compliance_status
        """).get_as_df()
        
        status_dict = dict(zip(result['compliance_status'], result['count']))
        assert status_dict['completed'] == 5
        assert status_dict['not_implemented'] == 5
        assert status_dict['partial'] == 1
        assert status_dict['planned'] == 1

    def test_priority_gap_analysis(self, db_with_comprehensive_data):
        """優先度の高いギャップ（Level 1の未実装）の分析が正しく動作すること"""
        # Find Level 1 gaps
        result = db_with_comprehensive_data.execute("""
            MATCH (ref:ReferenceEntity)
            WHERE ref.level = 1 AND NOT EXISTS {
                MATCH (:RequirementEntity)-[:IMPLEMENTS]->(ref)
            }
            RETURN ref.id, ref.section, ref.category, ref.description
            ORDER BY ref.category, ref.section
        """).get_as_df()
        
        assert len(result) == 3
        
        # All Level 1 gaps should be identified
        level1_gaps = result['ref.id'].tolist()
        assert 'ASVS-V2.1.3' in level1_gaps
        assert 'ASVS-V2.2.2' in level1_gaps
        assert 'ASVS-V4.1.3' in level1_gaps

    def test_implementation_progress_tracking(self, db_with_comprehensive_data):
        """実装進捗のトラッキングが正しく動作すること"""
        # Track implementation progress by status
        result = db_with_comprehensive_data.execute("""
            MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            WITH ref.category as category, impl.status as status
            RETURN 
                category,
                status,
                count(*) as count
            ORDER BY category, status
        """).get_as_df()
        
        # Verify authentication progress
        auth_data = result[result['category'] == 'authentication']
        auth_statuses = dict(zip(auth_data['status'], auth_data['count']))
        assert auth_statuses['completed'] == 3
        assert auth_statuses['partial'] == 1

    def test_requirement_coverage_analysis(self, db_with_comprehensive_data):
        """要件のカバレッジ分析（どの要件が何個の標準を実装しているか）"""
        result = db_with_comprehensive_data.execute("""
            MATCH (req:RequirementEntity)
            OPTIONAL MATCH (req)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
            WITH req, count(ref) as reference_count
            RETURN 
                req.uri,
                req.title,
                reference_count
            ORDER BY reference_count DESC, req.uri
        """).get_as_df()
        
        # Password policy should implement the most references
        assert result.iloc[0]['req.uri'] == 'req://auth/password-policy'
        assert result.iloc[0]['reference_count'] == 2
        
        # Some requirements implement nothing (gap in requirements)
        zero_impl = result[result['reference_count'] == 0]
        assert len(zero_impl) == 0  # All our requirements implement at least something

    def test_generate_gap_report(self, db_with_comprehensive_data):
        """ギャップレポートの生成が正しく動作すること"""
        # Generate comprehensive gap report
        report = db_with_comprehensive_data.execute("""
            WITH 
                // Total statistics
                (SELECT count(*) FROM ReferenceEntity) as total_references,
                (SELECT count(DISTINCT ref) FROM RequirementEntity-[:IMPLEMENTS]->(ref:ReferenceEntity)) as implemented_references,
                
                // Level 1 statistics
                (SELECT count(*) FROM ReferenceEntity WHERE level = 1) as level1_total,
                (SELECT count(DISTINCT ref) FROM RequirementEntity-[:IMPLEMENTS]->(ref:ReferenceEntity) WHERE ref.level = 1) as level1_implemented,
                
                // Category breakdown
                (SELECT ref.category as category, count(*) as gaps 
                 FROM ReferenceEntity ref
                 WHERE NOT EXISTS { MATCH (:RequirementEntity)-[:IMPLEMENTS]->(ref) }
                 GROUP BY ref.category) as category_gaps
                 
            RETURN 
                total_references,
                implemented_references,
                total_references - implemented_references as total_gaps,
                CAST(implemented_references AS DOUBLE) / CAST(total_references AS DOUBLE) * 100 as overall_coverage,
                level1_total,
                level1_implemented,
                level1_total - level1_implemented as level1_gaps,
                CAST(level1_implemented AS DOUBLE) / CAST(level1_total AS DOUBLE) * 100 as level1_coverage
        """).get_as_df()
        
        # Verify report statistics
        assert report.iloc[0]['total_references'] == 12
        assert report.iloc[0]['implemented_references'] == 7
        assert report.iloc[0]['total_gaps'] == 5
        assert report.iloc[0]['overall_coverage'] == pytest.approx(58.33, rel=0.01)
        assert report.iloc[0]['level1_gaps'] == 3
        assert report.iloc[0]['level1_coverage'] == 62.5