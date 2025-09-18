#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import kuzu
except ImportError:
    print("Error: kuzu module not found. Please run:")
    print("  nix develop")
    print("or")
    print("  nix shell .#default")
    sys.exit(1)

from crawler import find_module_files, load_module


def init_db(db_path: str = "./readme.db") -> None:
    """Initialize database with complete schema."""
    if Path(db_path).exists():
        import shutil
        shutil.rmtree(db_path)
    
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Complete schema with all fields
    conn.execute("""
        CREATE NODE TABLE Module(
            id STRING PRIMARY KEY,
            path STRING,
            purpose STRING,
            type STRING,
            version STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE DEPENDS_ON(FROM Module TO Module)
    """)
    
    conn.execute("""
        CREATE REL TABLE PARENT_OF(FROM Module TO Module)
    """)
    
    print(f"Initialized {db_path}")


def crawl_and_index(root_path: str, db_path: str = "./readme.db") -> int:
    """Crawl for module.json files and index them in KuzuDB."""
    init_db(db_path)
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    module_files = find_module_files(root_path)
    indexed_count = 0
    
    for file_path in module_files:
        module = load_module(file_path)
        if not module:
            continue
        
        # Insert module
        module_id = module.get('id', file_path.stem)
        conn.execute(
            f"""
            CREATE (m:Module {{
                id: '{module_id}',
                path: '{str(file_path.parent)}',
                purpose: '{module.get('purpose', '')}',
                type: '{module.get('type', 'unknown')}',
                version: '{module.get('version', '0.0.0')}'
            }})
            """
        )
        indexed_count += 1
    
    print(f"Indexed {indexed_count} modules")
    return indexed_count


def build_dependency_graph(root_path: str, db_path: str = "./readme.db") -> None:
    """Build dependency edges from module.json files."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    module_files = find_module_files(root_path)
    edge_count = 0
    
    for file_path in module_files:
        module = load_module(file_path)
        if not module:
            continue
        
        module_id = module.get('id', file_path.stem)
        dependencies = module.get('dependencies', [])
        
        for dep in dependencies:
            if isinstance(dep, dict):
                dep_id = dep.get('id')
            else:
                dep_id = dep
            
            if dep_id:
                try:
                    conn.execute(
                        f"""
                        MATCH (m:Module {{id: '{module_id}'}})
                        MATCH (d:Module {{id: '{dep_id}'}})
                        CREATE (m)-[:DEPENDS_ON]->(d)
                        """
                    )
                    edge_count += 1
                except:
                    pass  # Dependency not found
    
    print(f"Created {edge_count} dependency edges")


def build_hierarchy(root_path: str, db_path: str = "./readme.db") -> None:
    """Build parent-child relationships based on directory structure."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Get all modules
    result = conn.execute("MATCH (m:Module) RETURN m.id, m.path")
    modules = []
    while result.has_next():
        row = result.get_next()
        modules.append({'id': row[0], 'path': Path(row[1])})
    
    # Build hierarchy
    edge_count = 0
    for i, parent in enumerate(modules):
        for child in modules[i+1:]:
            if parent['path'] in child['path'].parents:
                try:
                    conn.execute(
                        f"""
                        MATCH (p:Module {{id: '{parent['id']}'}})
                        MATCH (c:Module {{id: '{child['id']}'}})
                        CREATE (p)-[:PARENT_OF]->(c)
                        """
                    )
                    edge_count += 1
                except:
                    pass
    
    print(f"Created {edge_count} hierarchy edges")


def detect_circular_deps(db_path: str = "./readme.db") -> List[List[str]]:
    """Detect circular dependencies."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    result = conn.execute("""
        MATCH path = (m:Module)-[:DEPENDS_ON*2..]->(m)
        RETURN DISTINCT m.id
    """)
    
    circular = []
    while result.has_next():
        circular.append(result.get_next()[0])
    
    return circular


def get_dependencies(module_id: str, db_path: str = "./readme.db") -> List[Dict[str, str]]:
    """Get all dependencies of a module."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    result = conn.execute(
        f"""
        MATCH (m:Module {{id: '{module_id}'}})-[:DEPENDS_ON]->(d:Module)
        RETURN d.id, d.type, d.purpose
        """
    )
    
    deps = []
    while result.has_next():
        row = result.get_next()
        deps.append({
            'id': row[0],
            'type': row[1],
            'purpose': row[2]
        })
    
    return deps


def get_dependents(module_id: str, db_path: str = "./readme.db") -> List[Dict[str, str]]:
    """Get all modules that depend on this module."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    result = conn.execute(
        f"""
        MATCH (m:Module {{id: '{module_id}'}})<-[:DEPENDS_ON]-(d:Module)
        RETURN d.id, d.type, d.purpose
        """
    )
    
    deps = []
    while result.has_next():
        row = result.get_next()
        deps.append({
            'id': row[0],
            'type': row[1],
            'purpose': row[2]
        })
    
    return deps


def query(cypher: str, db_path: str = "./readme.db") -> List[Any]:
    """Execute arbitrary Cypher query."""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    result = conn.execute(cypher)
    rows = []
    while result.has_next():
        rows.append(result.get_next())
    
    return rows


def query_live(root_path: str, cypher: str) -> List[Any]:
    """Execute query on in-memory database with dynamic module detection."""
    import tempfile
    import shutil
    
    # Create temporary directory for in-memory-like operation
    temp_dir = tempfile.mkdtemp(prefix="readme_graph_")
    temp_db = f"{temp_dir}/temp.db"
    
    try:
        # Initialize fresh database
        db = kuzu.Database(temp_db)
        conn = kuzu.Connection(db)
        
        # Create schema
        conn.execute("""
            CREATE NODE TABLE Module(
                id STRING PRIMARY KEY,
                path STRING,
                purpose STRING,
                type STRING,
                version STRING
            )
        """)
        
        conn.execute("""
            CREATE REL TABLE DEPENDS_ON(FROM Module TO Module)
        """)
        
        conn.execute("""
            CREATE REL TABLE PARENT_OF(FROM Module TO Module)
        """)
        
        # Find and index all modules
        module_files = find_module_files(root_path)
        modules_by_id = {}
        
        # First pass: create all nodes
        for file_path in module_files:
            module = load_module(file_path)
            if not module:
                continue
            
            module_id = module.get('id', file_path.stem)
            modules_by_id[module_id] = {
                'module': module,
                'path': file_path
            }
            
            # Escape single quotes in strings
            purpose = module.get('purpose', '').replace("'", "''")
            module_type = module.get('type', 'unknown').replace("'", "''")
            version = module.get('version', '0.0.0').replace("'", "''")
            path_str = str(file_path.parent).replace("'", "''")
            
            conn.execute(
                f"""
                CREATE (m:Module {{
                    id: '{module_id}',
                    path: '{path_str}',
                    purpose: '{purpose}',
                    type: '{module_type}',
                    version: '{version}'
                }})
                """
            )
        
        # Second pass: create dependency edges
        for module_id, data in modules_by_id.items():
            module = data['module']
            dependencies = module.get('dependencies', [])
            
            for dep in dependencies:
                if isinstance(dep, dict):
                    dep_id = dep.get('id')
                else:
                    dep_id = dep
                
                if dep_id and dep_id in modules_by_id:
                    try:
                        conn.execute(
                            f"""
                            MATCH (m:Module {{id: '{module_id}'}})
                            MATCH (d:Module {{id: '{dep_id}'}})
                            CREATE (m)-[:DEPENDS_ON]->(d)
                            """
                        )
                    except:
                        pass  # Dependency not found
        
        # Third pass: create hierarchy edges (based on path)
        module_list = list(modules_by_id.items())
        for i, (parent_id, parent_data) in enumerate(module_list):
            parent_path = parent_data['path'].parent
            for child_id, child_data in module_list[i+1:]:
                child_path = child_data['path'].parent
                if parent_path in child_path.parents:
                    try:
                        conn.execute(
                            f"""
                            MATCH (p:Module {{id: '{parent_id}'}})
                            MATCH (c:Module {{id: '{child_id}'}})
                            CREATE (p)-[:PARENT_OF]->(c)
                            """
                        )
                    except:
                        pass
        
        # Execute the user's query
        result = conn.execute(cypher)
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        
        return rows
        
    finally:
        # Clean up temporary database
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python readme_graph.py <command> [args]")
        print("Commands:")
        print("  index <path>           - Crawl and index all module.json files")
        print("  deps <path>            - Build dependency graph")
        print("  hierarchy <path>       - Build hierarchy relationships")
        print("  circular               - Detect circular dependencies")
        print("  get-deps <module_id>   - Get dependencies of a module")
        print("  get-dependents <id>    - Get modules depending on this")
        print("  query <cypher>         - Execute Cypher query")
        print("  query-live <path> <cypher> - Execute query on in-memory DB")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "index":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py index <path>")
            sys.exit(1)
        crawl_and_index(sys.argv[2])
    elif command == "deps":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py deps <path>")
            sys.exit(1)
        build_dependency_graph(sys.argv[2])
    elif command == "hierarchy":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py hierarchy <path>")
            sys.exit(1)
        build_hierarchy(sys.argv[2])
    elif command == "circular":
        circular = detect_circular_deps()
        if circular:
            print(f"Circular dependencies found: {circular}")
        else:
            print("No circular dependencies")
    elif command == "get-deps":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py get-deps <module_id>")
            sys.exit(1)
        deps = get_dependencies(sys.argv[2])
        for dep in deps:
            print(f"  → {dep['id']} ({dep['type']}): {dep['purpose']}")
    elif command == "get-dependents":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py get-dependents <module_id>")
            sys.exit(1)
        deps = get_dependents(sys.argv[2])
        for dep in deps:
            print(f"  ← {dep['id']} ({dep['type']}): {dep['purpose']}")
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python readme_graph.py query <cypher>")
            sys.exit(1)
        rows = query(sys.argv[2])
        for row in rows:
            print(row)
    elif command == "query-live":
        if len(sys.argv) < 4:
            print("Usage: python readme_graph.py query-live <path> <cypher>")
            sys.exit(1)
        rows = query_live(sys.argv[2], sys.argv[3])
        for row in rows:
            print(row)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)