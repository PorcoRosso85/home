#!/usr/bin/env python3
"""
Performance comparison test: Old vs New dependency implementation
Compares repository.add_dependency vs template add_dependency
"""
import time
import random
import string
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables to use in-memory database
os.environ['RGL_DB_PATH'] = ':memory:'
os.environ['RGL_SKIP_SCHEMA_CHECK'] = '1'


def generate_random_id(prefix="req_", length=6):
    """Generate a random requirement ID"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{suffix}"


def create_test_requirements(repo, count):
    """Create test requirements and return their IDs"""
    req_ids = []
    
    print(f"Creating {count} test requirements...")
    start_time = time.time()
    
    for i in range(count):
        req_id = generate_random_id()
        req_ids.append(req_id)
        
        # Use repository save method directly for efficiency
        result = repo["save"]({
            "id": req_id,
            "title": f"Test Requirement {i+1}",
            "description": f"Test requirement for performance testing #{i+1}",
            "status": "proposed"
        })
        
        if isinstance(result, dict) and result.get("type") == "DatabaseError":
            print(f"Error creating requirement: {result}")
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
        
        result = repo["add_dependency"](from_id, to_id, "depends_on", f"Test dependency {i+1}")
        
        if isinstance(result, dict) and result.get("success"):
            success_count += 1
        else:
            error_count += 1
            if circular and i == num_dependencies - 1:
                print(f"  Expected circular dependency error: {result.get('message', 'Unknown error')}")
    
    elapsed_time = time.time() - start_time
    
    print(f"  Completed in {elapsed_time:.3f} seconds")
    print(f"  Success: {success_count}, Errors: {error_count}")
    print(f"  Average time per dependency: {elapsed_time/num_dependencies:.4f}s")
    
    return elapsed_time


def test_new_implementation(repo, process_template, req_ids, num_dependencies, circular=False):
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
        
        input_data = {
            "template": "add_dependency",
            "parameters": {
                "from_id": from_id,
                "to_id": to_id,
                "dependency_type": "depends_on",
                "reason": f"Test dependency {i+1}"
            }
        }
        
        result = process_template(input_data, repo)
        
        if result.get("status") == "success":
            success_count += 1
        else:
            error_count += 1
            if circular and i == num_dependencies - 1:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"  Expected circular dependency error: {error_msg}")
    
    elapsed_time = time.time() - start_time
    
    print(f"  Completed in {elapsed_time:.3f} seconds")
    print(f"  Success: {success_count}, Errors: {error_count}")
    print(f"  Average time per dependency: {elapsed_time/num_dependencies:.4f}s")
    
    return elapsed_time


def run_comparison_test(node_count, dependency_ratio=0.5):
    """Run performance comparison for given node count"""
    
    # Import here to avoid issues at module level
    from infrastructure.kuzu_repository import create_kuzu_repository
    from application.template_processor import process_template
    
    print(f"\n{'='*60}")
    print(f"TESTING WITH {node_count} NODES")
    print(f"{'='*60}")
    
    # Create two separate repositories for fair comparison
    print("\nInitializing test repositories...")
    repo_old = create_kuzu_repository(":memory:")
    repo_new = create_kuzu_repository(":memory:")
    
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
    time_new = test_new_implementation(repo_new, process_template, req_ids_new, num_dependencies, circular=False)
    
    print(f"\nPerformance comparison (no circular):")
    print(f"  OLD implementation: {time_old:.3f}s")
    print(f"  NEW implementation: {time_new:.3f}s")
    
    if time_new < time_old:
        speedup = (time_old / time_new - 1) * 100
        print(f"  ✅ NEW is {speedup:.1f}% FASTER")
    else:
        slowdown = (time_new / time_old - 1) * 100
        print(f"  ❌ NEW is {slowdown:.1f}% SLOWER")
    
    # Test with circular dependency scenario
    print(f"\n--- Testing WITH circular dependency detection ---")
    
    # Reset repositories for circular test
    repo_old = create_kuzu_repository(":memory:")
    repo_new = create_kuzu_repository(":memory:")
    req_ids_old = create_test_requirements(repo_old, node_count)
    req_ids_new = create_test_requirements(repo_new, node_count)
    
    # Create a chain of dependencies for circular test
    print(f"\nCreating dependency chain for circular test...")
    for i in range(len(req_ids_old) - 1):
        repo_old["add_dependency"](req_ids_old[i], req_ids_old[i+1])
        
        input_data = {
            "template": "add_dependency",
            "parameters": {
                "from_id": req_ids_new[i],
                "to_id": req_ids_new[i+1]
            }
        }
        process_template(input_data, repo_new)
    
    # Now test adding a circular dependency
    time_old_circular = test_old_implementation(repo_old, req_ids_old, 1, circular=True)
    time_new_circular = test_new_implementation(repo_new, process_template, req_ids_new, 1, circular=True)
    
    print(f"\nCircular dependency detection performance:")
    print(f"  OLD implementation: {time_old_circular:.3f}s")
    print(f"  NEW implementation: {time_new_circular:.3f}s")
    
    if time_new_circular < time_old_circular:
        speedup = (time_old_circular / time_new_circular - 1) * 100
        print(f"  ✅ NEW is {speedup:.1f}% FASTER at detecting circular dependencies")
    else:
        slowdown = (time_new_circular / time_old_circular - 1) * 100
        print(f"  ❌ NEW is {slowdown:.1f}% SLOWER at detecting circular dependencies")


def main():
    """Run performance comparison tests"""
    print("PERFORMANCE COMPARISON: Old vs New Dependency Implementation")
    print("="*60)
    
    # Test with different graph sizes
    test_sizes = [10, 100, 1000]
    
    overall_results = []
    
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
    print("\nKey findings:")
    print("- Both implementations should perform similarly for basic operations")
    print("- Template implementation adds validation overhead but improves consistency")
    print("- Circular dependency detection performance depends on graph traversal efficiency")


if __name__ == "__main__":
    main()