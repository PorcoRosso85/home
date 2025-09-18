"""Use case for code analysis queries."""

from typing import List, Union, Optional, Dict, Any
from ..domain.symbol import Symbol
from ..domain.errors import ErrorDict, create_error, is_error
from ..infrastructure.kuzu_repository import KuzuRepository


def find_dead_code(repository: KuzuRepository) -> Union[List[Dict[str, Any]], ErrorDict]:
    """
    Find functions that are never called.
    
    Args:
        repository: KuzuDB repository
        
    Returns:
        List of dead code entries or error
    """
    query = """
        MATCH (s:Symbol)
        WHERE s.kind = 'function'
          AND NOT EXISTS {
              MATCH (s)<-[:CALLS]-()
          }
          AND s.name != 'main'
          AND NOT s.name STARTS WITH 'test_'
          AND NOT s.name STARTS WITH '__'
        RETURN s.name AS name, 
               s.location_uri AS location,
               s.kind AS kind
        ORDER BY s.location_uri
    """
    
    result = repository.execute_cypher(query)
    if is_error(result):
        return result
    
    dead_code = []
    for row in result:
        dead_code.append({
            'name': row[0],
            'location': row[1],
            'kind': row[2]
        })
    
    return dead_code


def find_most_called_functions(
    repository: KuzuRepository,
    limit: int = 10
) -> Union[List[Dict[str, Any]], ErrorDict]:
    """
    Find the most frequently called functions.
    
    Args:
        repository: KuzuDB repository
        limit: Number of results to return
        
    Returns:
        List of most called functions or error
    """
    query = """
        MATCH (s:Symbol)<-[c:CALLS]-()
        WHERE s.kind = 'function'
        WITH s, COUNT(c) AS call_count
        RETURN s.name AS name,
               s.location_uri AS location,
               call_count
        ORDER BY call_count DESC
        LIMIT $limit
    """
    
    result = repository.execute_cypher(query, {'limit': limit})
    if is_error(result):
        return result
    
    functions = []
    for row in result:
        functions.append({
            'name': row[0],
            'location': row[1],
            'call_count': row[2]
        })
    
    return functions


def find_circular_dependencies(
    repository: KuzuRepository,
    max_depth: int = 5
) -> Union[List[Dict[str, Any]], ErrorDict]:
    """
    Find circular dependencies between functions.
    
    Args:
        repository: KuzuDB repository
        max_depth: Maximum cycle depth to search
        
    Returns:
        List of circular dependencies or error
    """
    # Start with simple mutual recursion
    query = """
        MATCH (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(a)
        WHERE a.kind = 'function' AND b.kind = 'function'
          AND a.location_uri < b.location_uri
        RETURN a.name AS func1, 
               a.location_uri AS loc1,
               b.name AS func2,
               b.location_uri AS loc2
    """
    
    result = repository.execute_cypher(query)
    if is_error(result):
        return result
    
    cycles = []
    for row in result:
        cycles.append({
            'type': 'mutual_recursion',
            'functions': [
                {'name': row[0], 'location': row[1]},
                {'name': row[2], 'location': row[3]}
            ]
        })
    
    # TODO: Add detection for longer cycles
    
    return cycles


def get_file_dependencies(
    repository: KuzuRepository,
    file_path: str
) -> Union[Dict[str, Any], ErrorDict]:
    """
    Get dependencies for a specific file.
    
    Args:
        repository: KuzuDB repository
        file_path: Path to file
        
    Returns:
        Dependency information or error
    """
    # Normalize file path
    from pathlib import Path
    abs_path = Path(file_path).resolve()
    file_uri_prefix = f"file://{abs_path}#"
    
    # Get outgoing dependencies
    outgoing_query = """
        MATCH (from:Symbol)-[:CALLS]->(to:Symbol)
        WHERE from.location_uri STARTS WITH $prefix
          AND NOT to.location_uri STARTS WITH $prefix
        WITH DISTINCT substring(to.location_uri, 7, indexOf(to.location_uri, '#') - 7) AS dep_file
        RETURN dep_file
        ORDER BY dep_file
    """
    
    outgoing = repository.execute_cypher(outgoing_query, {'prefix': file_uri_prefix})
    if is_error(outgoing):
        return outgoing
    
    # Get incoming dependencies
    incoming_query = """
        MATCH (from:Symbol)-[:CALLS]->(to:Symbol)
        WHERE to.location_uri STARTS WITH $prefix
          AND NOT from.location_uri STARTS WITH $prefix
        WITH DISTINCT substring(from.location_uri, 7, indexOf(from.location_uri, '#') - 7) AS dep_file
        RETURN dep_file
        ORDER BY dep_file
    """
    
    incoming = repository.execute_cypher(incoming_query, {'prefix': file_uri_prefix})
    if is_error(incoming):
        return incoming
    
    return {
        'file': str(abs_path),
        'imports': [row[0] for row in outgoing],
        'imported_by': [row[0] for row in incoming]
    }


def get_complexity_metrics(repository: KuzuRepository) -> Union[Dict[str, Any], ErrorDict]:
    """
    Get various complexity metrics for the codebase.
    
    Args:
        repository: KuzuDB repository
        
    Returns:
        Complexity metrics or error
    """
    # Total counts
    counts_query = """
        MATCH (s:Symbol)
        WITH COUNT(s) AS total_symbols,
             SUM(CASE WHEN s.kind = 'function' THEN 1 ELSE 0 END) AS total_functions,
             SUM(CASE WHEN s.kind = 'class' THEN 1 ELSE 0 END) AS total_classes,
             SUM(CASE WHEN s.kind = 'method' THEN 1 ELSE 0 END) AS total_methods
        MATCH ()-[c:CALLS]->()
        WITH total_symbols, total_functions, total_classes, total_methods, COUNT(c) AS total_calls
        RETURN total_symbols, total_functions, total_classes, total_methods, total_calls
    """
    
    counts = repository.execute_cypher(counts_query)
    if is_error(counts):
        return counts
    
    if not counts:
        return {
            'total_symbols': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_methods': 0,
            'total_calls': 0
        }
    
    row = counts[0]
    
    # Most complex functions (by outgoing calls)
    complex_query = """
        MATCH (s:Symbol)-[c:CALLS]->()
        WHERE s.kind = 'function'
        WITH s, COUNT(c) AS out_calls
        RETURN s.name, s.location_uri, out_calls
        ORDER BY out_calls DESC
        LIMIT 5
    """
    
    complex_funcs = repository.execute_cypher(complex_query)
    if is_error(complex_funcs):
        return complex_funcs
    
    return {
        'total_symbols': row[0] if row[0] else 0,
        'total_functions': row[1] if row[1] else 0,
        'total_classes': row[2] if row[2] else 0,
        'total_methods': row[3] if row[3] else 0,
        'total_calls': row[4] if row[4] else 0,
        'most_complex_functions': [
            {
                'name': func[0],
                'location': func[1],
                'outgoing_calls': func[2]
            }
            for func in complex_funcs
        ]
    }


def create_analysis_report(
    repository: KuzuRepository,
    output_format: str = 'json'
) -> Union[Dict[str, Any], ErrorDict]:
    """
    Create a comprehensive analysis report.
    
    Args:
        repository: KuzuDB repository
        output_format: Output format (currently only 'json')
        
    Returns:
        Analysis report or error
    """
    report = {}
    
    # Get complexity metrics
    metrics = get_complexity_metrics(repository)
    if is_error(metrics):
        return metrics
    report['metrics'] = metrics
    
    # Find dead code
    dead_code = find_dead_code(repository)
    if is_error(dead_code):
        return dead_code
    report['dead_code'] = dead_code
    
    # Find most called functions
    most_called = find_most_called_functions(repository, limit=10)
    if is_error(most_called):
        return most_called
    report['most_called_functions'] = most_called
    
    # Find circular dependencies
    cycles = find_circular_dependencies(repository)
    if is_error(cycles):
        return cycles
    report['circular_dependencies'] = cycles
    
    return report