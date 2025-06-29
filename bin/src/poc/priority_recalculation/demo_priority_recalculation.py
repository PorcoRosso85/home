"""
Priority Recalculation Demo
優先順位再計算のデモンストレーション
"""
import kuzu
from priority_recalculation_simple import register_simple_priority_udfs


def main():
    # Create in-memory database
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    print("🚀 Priority Recalculation UDF Demo")
    print("=" * 50)
    
    # Create schema
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            priority UINT8 DEFAULT 128
        )
    """)
    
    # Insert initial requirements
    requirements = [
        ("REQ-001", "User Authentication", 50),
        ("REQ-002", "Database Connection", 100),
        ("REQ-003", "API Gateway", 150),
        ("REQ-004", "Frontend UI", 200),
        ("REQ-005", "Logging System", 250),
    ]
    
    for id, title, priority in requirements:
        conn.execute(f"CREATE (:RequirementEntity {{id: '{id}', title: '{title}', priority: {priority}}})")
    
    # Register UDFs
    register_simple_priority_udfs(conn)
    
    # Show initial state
    print("\n📋 Initial Priorities:")
    result = conn.execute("MATCH (r:RequirementEntity) RETURN r.id, r.title, r.priority ORDER BY r.priority")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1]:<25} Priority: {row[2]:>3}")
    
    # Scenario 1: Compress priorities to make room for urgent requirement
    print("\n🔄 Scenario 1: Compressing priorities by 70% to make room...")
    conn.execute("""
        MATCH (r:RequirementEntity)
        WITH r, calc_compressed_priority(r.priority, 0.7) AS new_p
        SET r.priority = new_p
    """)
    
    # Add urgent requirement
    conn.execute("""
        CREATE (:RequirementEntity {
            id: 'REQ-URGENT',
            title: 'Critical Security Fix',
            priority: 255
        })
    """)
    
    # Show compressed state
    result = conn.execute("MATCH (r:RequirementEntity) RETURN r.id, r.title, r.priority ORDER BY r.priority DESC")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1]:<25} Priority: {row[2]:>3}")
    
    # Scenario 2: Normalize priorities to use full range
    print("\n🔄 Scenario 2: Normalizing priorities to use full 0-255 range...")
    result = conn.execute("""
        MATCH (r:RequirementEntity)
        WITH min(r.priority) AS min_p, max(r.priority) AS max_p
        MATCH (r:RequirementEntity)
        WITH r, min_p, max_p, calc_normalized_priority(r.priority, min_p, max_p, 0, 255) AS new_p
        SET r.priority = new_p
        RETURN r.id, r.title, r.priority
        ORDER BY r.priority DESC
    """)
    
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1]:<25} Priority: {row[2]:>3}")
    
    # Scenario 3: Find gap for medium priority requirement
    print("\n🔍 Scenario 3: Finding optimal gap for medium priority requirement...")
    
    # Get current priorities as string
    result = conn.execute("MATCH (r:RequirementEntity) RETURN r.priority ORDER BY r.priority")
    priorities = []
    while result.has_next():
        priorities.append(str(result.get_next()[0]))
    priorities_str = ','.join(priorities)
    
    # Find gap for priority 128
    result = conn.execute(f"RETURN find_gap_position(128, '{priorities_str}') AS gap_pos")
    gap_pos = result.get_next()[0]
    print(f"  Optimal position for priority 128: {gap_pos}")
    
    # Add new requirement at gap position
    conn.execute(f"""
        CREATE (:RequirementEntity {{
            id: 'REQ-006',
            title: 'Performance Monitoring',
            priority: {gap_pos}
        }})
    """)
    
    # Show final state
    print("\n📊 Final State (sorted by priority):")
    result = conn.execute("MATCH (r:RequirementEntity) RETURN r.id, r.title, r.priority ORDER BY r.priority DESC")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1]:<25} Priority: {row[2]:>3}")
    
    # Show priority distribution
    print("\n📈 Priority Distribution:")
    result = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN count(r) AS total,
               min(r.priority) AS min_priority,
               max(r.priority) AS max_priority,
               avg(r.priority) AS avg_priority
    """)
    row = result.get_next()
    print(f"  Total Requirements: {row[0]}")
    print(f"  Min Priority: {row[1]}")
    print(f"  Max Priority: {row[2]}")
    print(f"  Avg Priority: {row[3]:.1f}")
    
    print("\n✅ Demo Complete!")


if __name__ == "__main__":
    main()