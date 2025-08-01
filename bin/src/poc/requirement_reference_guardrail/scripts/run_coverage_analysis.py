#!/usr/bin/env python3
"""
Run coverage analysis queries to understand requirement reference compliance.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List
import kuzu
from log_py import log

def load_queries(query_file: Path) -> List[Dict[str, str]]:
    """Load queries from the Cypher file."""
    queries = []
    current_query = []
    current_comment = ""
    
    with open(query_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("// Query"):
                if current_query:
                    queries.append({
                        "description": current_comment,
                        "query": '\n'.join(current_query)
                    })
                current_comment = line[3:].strip()
                current_query = []
            elif line and not line.startswith("//"):
                current_query.append(line)
    
    # Don't forget the last query
    if current_query:
        queries.append({
            "description": current_comment,
            "query": '\n'.join(current_query)
        })
    
    return queries

def run_analysis(db_path: str):
    """Run coverage analysis queries."""
    query_file = Path(__file__).parent / "coverage_analysis.cypher"
    
    # Create database connection
    db_result = kuzu.Database(db_path)
    if not isinstance(db_result, kuzu.Database):
        log("error", {"message": "Failed to open database", "error": db_result.message})
        return 1
    
    db = db_result
    conn_result = db.connect()
    if not isinstance(conn_result, kuzu.Connection):
        log("error", {"message": "Failed to connect to database", "error": conn_result.message})
        return 1
    
    conn = conn_result
    
    log("info", {"message": "Starting Requirement Reference Guardrail Coverage Analysis"})
    log("info", {"message": "=" * 60})
    
    # Load and run queries
    queries = load_queries(query_file)
    
    for i, query_info in enumerate(queries, 1):
        log("info", {"message": query_info['description']})
        log("info", {"message": "-" * 60})
        
        try:
            result = conn.execute(query_info['query'])
            if hasattr(result, 'get_as_arrow'):
                arrow_table = result.get_as_arrow()
                if arrow_table and arrow_table.num_rows > 0:
                    # Convert to pandas for nice display
                    df = arrow_table.to_pandas()
                    # Log the results row by row for structured output
                    for _, row in df.iterrows():
                        log("info", {"message": "Query result", **row.to_dict()})
                else:
                    log("info", {"message": "No results found"})
            else:
                log("info", {"message": "Query executed successfully"})
        except Exception as e:
            log("error", {"message": "Error executing query", "error": str(e), "query": query_info['description']})
    
    log("info", {"message": "=" * 60})
    log("info", {"message": "Analysis complete"})
    
    return 0

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        log("error", {
            "message": "Missing database path argument",
            "usage": "python run_coverage_analysis.py <database_path>",
            "example": "python run_coverage_analysis.py /tmp/req_guardrail.db"
        })
        return 1
    
    db_path = sys.argv[1]
    if not Path(db_path).exists():
        log("error", {
            "message": "Database not found",
            "path": db_path,
            "note": "Please create a database and import data first"
        })
        return 1
    
    return run_analysis(db_path)

if __name__ == "__main__":
    sys.exit(main())