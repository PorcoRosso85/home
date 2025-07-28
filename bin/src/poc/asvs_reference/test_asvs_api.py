"""
Tests for ASVS API

Validates the data provider interface for other POCs.
"""
import pytest
from asvs_api import ASVSDataProvider, create_asvs_provider
from asvs_types import SearchFilter


class TestASVSAPI:
    """Test ASVS data provider API"""
    
    @pytest.fixture
    def provider_with_data(self):
        """Create provider with sample data"""
        provider = create_asvs_provider(":memory:")
        conn = provider.conn
        
        # Create schema
        conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Requirement (
            uri STRING PRIMARY KEY,
            number STRING,
            description STRING,
            level1 BOOLEAN,
            level2 BOOLEAN,
            level3 BOOLEAN,
            section_uri STRING
        )
        """)
        
        conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Section (
            uri STRING PRIMARY KEY,
            number STRING,
            name STRING
        )
        """)
        
        conn.execute("""
        CREATE REL TABLE IF NOT EXISTS HAS_REQUIREMENT (
            FROM Section TO Requirement
        )
        """)
        
        # Insert sample data
        conn.execute("""
        CREATE (s:Section {uri: 'asvs:5.0:sec:2.1', number: '2.1', name: 'Password Security'})
        """)
        
        conn.execute("""
        CREATE (r1:Requirement {
            uri: 'asvs:5.0:req:2.1.1',
            number: '2.1.1',
            description: 'Verify that user set passwords are at least 12 characters in length',
            level1: true,
            level2: true,
            level3: true,
            section_uri: 'asvs:5.0:sec:2.1'
        })
        """)
        
        conn.execute("""
        CREATE (r2:Requirement {
            uri: 'asvs:5.0:req:2.1.2',
            number: '2.1.2',
            description: 'Verify that passwords of at least 64 characters are permitted',
            level1: true,
            level2: true,
            level3: true,
            section_uri: 'asvs:5.0:sec:2.1'
        })
        """)
        
        conn.execute("""
        CREATE (r3:Requirement {
            uri: 'asvs:5.0:req:2.1.3',
            number: '2.1.3',
            description: 'Verify that password truncation is not performed',
            level1: false,
            level2: true,
            level3: true,
            section_uri: 'asvs:5.0:sec:2.1'
        })
        """)
        
        # Create relationships
        conn.execute("""
        MATCH (s:Section {number: '2.1'}), (r:Requirement)
        WHERE r.section_uri = s.uri
        CREATE (s)-[:HAS_REQUIREMENT]->(r)
        """)
        
        return provider
    
    def test_get_requirement_by_number_success(self, provider_with_data):
        """Test getting requirement by number"""
        response = provider_with_data.get_requirement_by_number("2.1.1")
        
        assert response['type'] == 'Success'
        requirement = response['value']
        assert requirement['number'] == '2.1.1'
        assert requirement['description'] == 'Verify that user set passwords are at least 12 characters in length'
        assert requirement['level1'] is True
    
    def test_get_requirement_by_number_not_found(self, provider_with_data):
        """Test getting non-existent requirement"""
        response = provider_with_data.get_requirement_by_number("9.9.9")
        
        assert response['type'] == 'Error'
        assert response['error'] == 'NotFound'
        assert '9.9.9' in response['message']
    
    def test_search_requirements_by_keyword(self, provider_with_data):
        """Test searching requirements by keyword"""
        filter: SearchFilter = {'keyword': 'password'}
        response = provider_with_data.search_requirements(filter)
        
        assert response['type'] == 'Success'
        result = response['value']
        assert result['total_count'] == 3
        assert len(result['requirements']) == 3
        assert all('password' in req['description'].lower() for req in result['requirements'])
    
    def test_search_requirements_by_level(self, provider_with_data):
        """Test filtering by ASVS level"""
        filter: SearchFilter = {'levels': {'level1': True}}
        response = provider_with_data.search_requirements(filter)
        
        assert response['type'] == 'Success'
        result = response['value']
        assert result['total_count'] == 2  # Only 2.1.1 and 2.1.2
        assert all(req['level1'] is True for req in result['requirements'])
    
    def test_get_requirements_by_level(self, provider_with_data):
        """Test getting requirements by specific level"""
        response = provider_with_data.get_requirements_by_level(1)
        
        assert response['type'] == 'Success'
        result = response['value']
        assert result['total_count'] == 2
        
        # Test invalid level
        response = provider_with_data.get_requirements_by_level(4)
        assert response['type'] == 'Error'
        assert response['error'] == 'ValidationError'
    
    def test_get_requirements_by_section(self, provider_with_data):
        """Test getting requirements by section"""
        response = provider_with_data.get_requirements_by_section("2.1")
        
        assert response['type'] == 'Success'
        requirements = response['value']
        assert len(requirements) == 3
        assert all(req['number'].startswith('2.1.') for req in requirements)
    
    def test_search_with_pagination(self, provider_with_data):
        """Test search with pagination"""
        filter: SearchFilter = {'limit': 2, 'offset': 0}
        response = provider_with_data.search_requirements(filter)
        
        assert response['type'] == 'Success'
        result = response['value']
        assert len(result['requirements']) == 2
        assert result['total_count'] == 3
        
        # Get next page
        filter['offset'] = 2
        response = provider_with_data.search_requirements(filter)
        result = response['value']
        assert len(result['requirements']) == 1
    
    def test_error_handling(self):
        """Test error handling for database issues"""
        provider = ASVSDataProvider("invalid/path/to/db")
        
        # Should handle initialization errors gracefully
        try:
            response = provider.get_requirement_by_number("2.1.1")
            assert response['type'] == 'Error' or 'Failed' in str(response)
        except Exception as e:
            # Expected - invalid database path
            assert 'Failed to create repository' in str(e)