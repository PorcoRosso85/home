#!/usr/bin/env python3
"""
Standalone Performance comparison test: Old vs New dependency implementation
This version directly implements the minimal required functionality to avoid import issues.
"""
import time
import random
import string
import kuzu


def generate_random_id(prefix="req_", length=6):
    """Generate a random requirement ID"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{suffix}"


class SimpleRepository:
    """Minimal repository implementation for testing"""
    
    def __init__(self):
        self.db = kuzu.Database(":memory:")
        self.conn = kuzu.Connection(self.db)
        self._init_schema()
    
    def _init_schema(self):
        """Initialize the schema"""
        # Create RequirementEntity node table
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                status STRING,
                original_id STRING,
                version INT64
            )
        """)
        
        # Create DEPENDS_ON relationship table  
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (
                FROM RequirementEntity TO RequirementEntity,
                dependency_type STRING,
                reason STRING
            )
        """)
    
    def save(self, requirement):
        """Save a requirement"""
        try:
            self.conn.execute("""
                CREATE (r:RequirementEntity {
                    id: $id,
                    title: $title,
                    description: $description,
                    status: $status,
                    original_id: $id,
                    version: 1
                })
            """, {
                "id": requirement["id"],
                "title": requirement["title"],
                "description": requirement["description"],
                "status": requirement["status"]
            })
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    def add_dependency_old(self, from_id, to_id, dependency_type="depends_on", reason=""):
        """Old implementation: Direct dependency addition with circular check"""
        try:
            # Self dependency check
            if from_id == to_id:
                return {"error": "Self dependency not allowed"}
            
            # Circular dependency check
            cycle_check = self.conn.execute("""
                MATCH (from:RequirementEntity {id: $to_id})-[:DEPENDS_ON*]->(to:RequirementEntity {id: $from_id})
                RETURN count(*) > 0 as has_cycle
            """, {"from_id": from_id, "to_id": to_id})
            
            if cycle_check.has_next() and cycle_check.get_next()[0]:
                return {"error": f"Circular dependency detected: {from_id} -> {to_id}"}
            
            # Add dependency
            self.conn.execute("""
                MATCH (from:RequirementEntity {id: $from_id})
                MATCH (to:RequirementEntity {id: $to_id})
                CREATE (from)-[:DEPENDS_ON {dependency_type: $type, reason: $reason}]->(to)
            """, {
                "from_id": from_id,
                "to_id": to_id,
                "type": dependency_type,
                "reason": reason
            })
            
            return {"success": True}
            
        except Exception as e:
            return {"error": str(e)}
    
    def add_dependency_new(self, from_id, to_id, dependency_type="depends_on", reason=""):
        """New implementation: Template-based with pre-validation"""
        try:
            # Get all existing dependencies for validation
            all_deps = {}
            deps_result = self.conn.execute("""
                MATCH (from:RequirementEntity)-[d:DEPENDS_ON]->(to:RequirementEntity)
                RETURN from.id, to.id
            """)
            
            while deps_result.has_next():
                row = deps_result.get_next()
                dep_from = row[0]
                dep_to = row[1]
                if dep_from not in all_deps:
                    all_deps[dep_from] = []
                all_deps[dep_from].append(dep_to)
            
            # Check for circular dependency using DFS
            def has_path(graph, start, end, visited=None):
                if visited is None:
                    visited = set()
                if start == end:
                    return True
                if start in visited:
                    return False
                visited.add(start)
                for neighbor in graph.get(start, []):
                    if has_path(graph, neighbor, end, visited):
                        return True
                return False
            
            # Check if adding this edge would create a cycle
            if has_path(all_deps, to_id, from_id):
                return {"error": f"Circular dependency detected: {from_id} -> {to_id}", "status": "error"}
            
            # Add the dependency using template-style parameters
            self.conn.execute("""
                MATCH (child:RequirementEntity {id: $child_id})
                MATCH (parent:RequirementEntity {id: $parent_id})
                CREATE (child)-[:DEPENDS_ON {dependency_type: $type, reason: $reason}]->(parent)
            """, {
                "child_id": from_id,  # Note: parameter naming difference
                "parent_id": to_id,
                "type": dependency_type,
                "reason": reason
            })
            
            return {"status": "success"}
            
        except Exception as e:
            return {"error": str(e), "status": "error"}


def create_test_requirements(repo, count):
    """Create test requirements and return their IDs"""
    req_ids = []
    
    print(f"Creating {count} test requirements...")
    start_time = time.time()
    
    for i in range(count):
        req_id = generate_random_id()
        req_ids.append(req_id)
        
        result = repo.save({
            "id": req_id,
            "title": f"Test Requirement {i+1}",
            "description": f"Test requirement for performance testing #{i+1}",
            "status": "proposed"
        })
        
        if "error" in result:
            print(f"Error creating requirement: {result['error']}")
            return []
    
    creation_time = time.time() - start_time
    print(f"Created {count} requirements in {creation_time:.3f} seconds ({creation_time/count:.4f}s per requirement)")
    
    return req_ids


def test_old_implementation(repo, req_ids, num_dependencies, circular=False):
    """Test performance using old repository.add_dependency method"""
    print(f"\nTesting OLD implementation (repository.add_dependency)...")
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    for i in range(num_dependencies):
        if circular and i == num_dependencies - 1:
            # Create circular dependency on last iteration
            from_id = req_ids[-1]
            to_id = req_ids[0]
        else:
            # Random non-circular dependency
            from_idx = random.randint(0, len(req_ids) - 2)
            to_idx = random.randint(from_idx + 1, len(req_ids) - 1)
            from_id = req_ids[from_idx]
            to_id = req_ids[to_idx]
        
        result = repo.add_dependency_old(from_id, to_id, "depends_on", f"Test dependency {i+1}")
        
        if result.get("success"):
            success_count += 1
        else:
            error_count += 1
            if circular and i == num_dependencies - 1:
                print(f"  Expected circular dependency error: {result.get('error', 'Unknown error')}")
    
    elapsed_time = time.time() - start_time
    
    print(f"  Completed in {elapsed_time:.3f} seconds")
    print(f"  Success: {success_count}, Errors: {error_count}")
    print(f"  Average time per dependency: {elapsed_time/num_dependencies:.4f}s")
    
    return elapsed_time


def test_new_implementation(repo, req_ids, num_dependencies, circular=False):
    """Test performance using new template add_dependency method"""
    print(f"\nTesting NEW implementation (template add_dependency)...")
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    for i in range(num_dependencies):
        if circular and i == num_dependencies - 1:
            # Create circular dependency on last iteration
            from_id = req_ids[-1]
            to_id = req_ids[0]
        else:
            # Random non-circular dependency
            from_idx = random.randint(0, len(req_ids) - 2)
            to_idx = random.randint(from_idx + 1, len(req_ids) - 1)
            from_id = req_ids[from_idx]
            to_id = req_ids[to_idx]
        
        result = repo.add_dependency_new(from_id, to_id, "depends_on", f"Test dependency {i+1}")
        
        if result.get("status") == "success":
            success_count += 1
        else:
            error_count += 1
            if circular and i == num_dependencies - 1:
                print(f"  Expected circular dependency error: {result.get('error', 'Unknown error')}")
    
    elapsed_time = time.time() - start_time
    
    print(f"  Completed in {elapsed_time:.3f} seconds")
    print(f"  Success: {success_count}, Errors: {error_count}")
    print(f"  Average time per dependency: {elapsed_time/num_dependencies:.4f}s")
    
    return elapsed_time


def run_comparison_test(node_count, dependency_ratio=0.5):
    """Run performance comparison for given node count"""
    print(f"\n{'='*60}")
    print(f"TESTING WITH {node_count} NODES")
    print(f"{'='*60}")
    
    # Create two separate repositories for fair comparison
    print("\nInitializing test repositories...")
    repo_old = SimpleRepository()
    repo_new = SimpleRepository()
    
    # Create requirements in both repositories
    req_ids_old = create_test_requirements(repo_old, node_count)
    req_ids_new = create_test_requirements(repo_new, node_count)
    
    if not req_ids_old or not req_ids_new:
        print("Failed to create test requirements")
        return
    
    num_dependencies = int(node_count * dependency_ratio)
    print(f"\nTesting with {num_dependencies} dependencies ({dependency_ratio*100:.0f}% of nodes)")
    
    # Test without circular dependencies
    print(f"\n--- Testing WITHOUT circular dependencies ---")
    time_old = test_old_implementation(repo_old, req_ids_old, num_dependencies, circular=False)
    time_new = test_new_implementation(repo_new, req_ids_new, num_dependencies, circular=False)
    
    print(f"\nPerformance comparison (no circular):")
    print(f"  OLD implementation: {time_old:.3f}s")
    print(f"  NEW implementation: {time_new:.3f}s")
    
    if time_new < time_old:
        speedup = (time_old / time_new - 1) * 100
        print(f"  ✅ NEW is {speedup:.1f}% FASTER")
    elif time_old < time_new:
        slowdown = (time_new / time_old - 1) * 100
        print(f"  ❌ NEW is {slowdown:.1f}% SLOWER")
    else:
        print(f"  ⚖️  Both implementations have similar performance")
    
    # Test with circular dependency scenario
    print(f"\n--- Testing WITH circular dependency detection ---")
    
    # Reset repositories for circular test
    repo_old = SimpleRepository()
    repo_new = SimpleRepository()
    req_ids_old = create_test_requirements(repo_old, node_count)
    req_ids_new = create_test_requirements(repo_new, node_count)
    
    # Create a chain of dependencies for circular test
    print(f"\nCreating dependency chain for circular test...")
    for i in range(len(req_ids_old) - 1):
        repo_old.add_dependency_old(req_ids_old[i], req_ids_old[i+1])
        repo_new.add_dependency_new(req_ids_new[i], req_ids_new[i+1])
    
    # Now test adding a circular dependency
    time_old_circular = test_old_implementation(repo_old, req_ids_old, 1, circular=True)
    time_new_circular = test_new_implementation(repo_new, req_ids_new, 1, circular=True)
    
    print(f"\nCircular dependency detection performance:")
    print(f"  OLD implementation: {time_old_circular:.3f}s")
    print(f"  NEW implementation: {time_new_circular:.3f}s")
    
    if time_new_circular < time_old_circular:
        speedup = (time_old_circular / time_new_circular - 1) * 100
        print(f"  ✅ NEW is {speedup:.1f}% FASTER at detecting circular dependencies")
    elif time_old_circular < time_new_circular:
        slowdown = (time_new_circular / time_old_circular - 1) * 100
        print(f"  ❌ NEW is {slowdown:.1f}% SLOWER at detecting circular dependencies")
    else:
        print(f"  ⚖️  Both implementations have similar circular detection performance")


def main():
    """Run performance comparison tests"""
    print("PERFORMANCE COMPARISON: Old vs New Dependency Implementation")
    print("="*60)
    
    # Test with different graph sizes
    test_sizes = [10, 100, 1000]
    
    for size in test_sizes:
        try:
            run_comparison_test(size)
        except Exception as e:
            print(f"\nError testing with {size} nodes: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\nThe performance comparison tests measure:")
    print("1. Time to create dependencies in graphs of different sizes")
    print("2. Time to detect circular dependencies")
    print("3. Average time per operation")
    print("\nKey differences between implementations:")
    print("- OLD: Uses direct graph traversal in database for circular detection")
    print("- NEW: Pre-fetches all dependencies and validates in-memory")
    print("\nPerformance characteristics:")
    print("- For small graphs: Similar performance")
    print("- For large graphs: NEW may be slower due to fetching all dependencies")
    print("- Circular detection: OLD may be faster for deep chains")


if __name__ == "__main__":
    main()