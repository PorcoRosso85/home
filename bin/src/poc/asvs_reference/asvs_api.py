"""
ASVS Reference API

Provides clean API for other POCs to access ASVS data.
Acts as a data provider with type-safe interfaces.
"""
from typing import List, Optional, Dict, Any
import kuzu
from pathlib import Path

from asvs_types import (
    ASVSRequirement, ASVSSection, ASVSChapter,
    RequirementSearchResult, APIResponse,
    SearchFilter, LevelFilter
)
from reference_repository import create_reference_repository


class ASVSDataProvider:
    """ASVS data provider for other POCs"""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize the data provider
        
        Args:
            db_path: Path to database or :memory: for in-memory
        """
        self.db_path = db_path
        self._repo = None
    
    @property
    def repo(self):
        """Lazy initialization of repository"""
        if self._repo is None:
            result = create_reference_repository(self.db_path)
            if isinstance(result, dict) and result.get("type") in ["DatabaseError", "ValidationError"]:
                raise Exception(f"Failed to create repository: {result['message']}")
            self._repo = result
        return self._repo
    
    @property
    def conn(self) -> kuzu.Connection:
        """Get database connection"""
        return self.repo["connection"]
    
    def get_requirement_by_number(self, number: str) -> APIResponse:
        """Get a specific requirement by its number
        
        Args:
            number: Requirement number (e.g., "2.1.1")
            
        Returns:
            APIResponse with ASVSRequirement or error
        """
        try:
            query = """
            MATCH (r:Requirement {number: $number})
            RETURN r.uri as uri, r.number as number, r.description as description,
                   r.level1 as level1, r.level2 as level2, r.level3 as level3,
                   r.section_uri as section_uri
            """
            result = self.conn.execute(query, {"number": number})
            
            if result.has_next():
                row = result.get_next()
                requirement: ASVSRequirement = {
                    'uri': row[0],
                    'number': row[1],
                    'description': row[2],
                    'level1': row[3],
                    'level2': row[4],
                    'level3': row[5],
                    'section_uri': row[6],
                    'tags': None,
                    'cwe': None,
                    'nist': None
                }
                return {'type': 'Success', 'value': requirement}
            else:
                return {
                    'type': 'Error',
                    'error': 'NotFound',
                    'message': f'Requirement {number} not found',
                    'details': {'number': number}
                }
        except Exception as e:
            return {
                'type': 'Error',
                'error': 'DatabaseError',
                'message': str(e),
                'details': None
            }
    
    def search_requirements(self, filter: SearchFilter) -> APIResponse:
        """Search requirements with filters
        
        Args:
            filter: Search filter options
            
        Returns:
            APIResponse with RequirementSearchResult or error
        """
        try:
            # Build WHERE clauses
            where_clauses = []
            params = {}
            
            if filter.get('keyword'):
                where_clauses.append("r.description =~ $keyword")
                params['keyword'] = f".*{filter['keyword']}.*"
            
            if filter.get('levels'):
                level_filter = filter['levels']
                if level_filter.get('level1') is not None:
                    where_clauses.append("r.level1 = $level1")
                    params['level1'] = level_filter['level1']
                if level_filter.get('level2') is not None:
                    where_clauses.append("r.level2 = $level2")
                    params['level2'] = level_filter['level2']
                if level_filter.get('level3') is not None:
                    where_clauses.append("r.level3 = $level3")
                    params['level3'] = level_filter['level3']
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "true"
            
            # Count query
            count_query = f"""
            MATCH (r:Requirement)
            WHERE {where_clause}
            RETURN count(r) as total
            """
            count_result = self.conn.execute(count_query, params).get_next()[0]
            
            # Data query with pagination
            limit = filter.get('limit', 100)
            offset = filter.get('offset', 0)
            
            data_query = f"""
            MATCH (r:Requirement)
            WHERE {where_clause}
            RETURN r.uri as uri, r.number as number, r.description as description,
                   r.level1 as level1, r.level2 as level2, r.level3 as level3,
                   r.section_uri as section_uri
            ORDER BY r.number
            LIMIT $limit OFFSET $offset
            """
            params['limit'] = limit
            params['offset'] = offset
            
            result = self.conn.execute(data_query, params)
            requirements: List[ASVSRequirement] = []
            
            while result.has_next():
                row = result.get_next()
                requirements.append({
                    'uri': row[0],
                    'number': row[1],
                    'description': row[2],
                    'level1': row[3],
                    'level2': row[4],
                    'level3': row[5],
                    'section_uri': row[6],
                    'tags': None,
                    'cwe': None,
                    'nist': None
                })
            
            search_result: RequirementSearchResult = {
                'requirements': requirements,
                'total_count': count_result,
                'query': filter.get('keyword', '')
            }
            
            return {'type': 'Success', 'value': search_result}
            
        except Exception as e:
            return {
                'type': 'Error',
                'error': 'SearchError',
                'message': str(e),
                'details': filter
            }
    
    def get_requirements_by_level(self, level: int) -> APIResponse:
        """Get all requirements for a specific ASVS level
        
        Args:
            level: ASVS level (1, 2, or 3)
            
        Returns:
            APIResponse with list of ASVSRequirements or error
        """
        if level not in [1, 2, 3]:
            return {
                'type': 'Error',
                'error': 'ValidationError',
                'message': 'Level must be 1, 2, or 3',
                'details': {'level': level}
            }
        
        level_field = f'level{level}'
        filter: SearchFilter = {
            'levels': {level_field: True}  # type: ignore
        }
        
        return self.search_requirements(filter)
    
    def get_requirements_by_section(self, section_number: str) -> APIResponse:
        """Get all requirements in a section
        
        Args:
            section_number: Section number (e.g., "2.1")
            
        Returns:
            APIResponse with list of ASVSRequirements or error
        """
        try:
            query = """
            MATCH (s:Section {number: $section_number})-[:HAS_REQUIREMENT]->(r:Requirement)
            RETURN r.uri as uri, r.number as number, r.description as description,
                   r.level1 as level1, r.level2 as level2, r.level3 as level3,
                   r.section_uri as section_uri
            ORDER BY r.number
            """
            result = self.conn.execute(query, {"section_number": section_number})
            requirements: List[ASVSRequirement] = []
            
            while result.has_next():
                row = result.get_next()
                requirements.append({
                    'uri': row[0],
                    'number': row[1],
                    'description': row[2],
                    'level1': row[3],
                    'level2': row[4],
                    'level3': row[5],
                    'section_uri': row[6],
                    'tags': None,
                    'cwe': None,
                    'nist': None
                })
            
            if requirements:
                return {'type': 'Success', 'value': requirements}
            else:
                return {
                    'type': 'Error',
                    'error': 'NotFound',
                    'message': f'No requirements found for section {section_number}',
                    'details': {'section_number': section_number}
                }
                
        except Exception as e:
            return {
                'type': 'Error',
                'error': 'DatabaseError',
                'message': str(e),
                'details': None
            }


# Convenience functions for simple usage
def create_asvs_provider(db_path: str = ":memory:") -> ASVSDataProvider:
    """Create an ASVS data provider instance"""
    return ASVSDataProvider(db_path)