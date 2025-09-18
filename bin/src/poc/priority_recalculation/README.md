# Priority Recalculation POC

This POC demonstrates how to implement priority recalculation logic using KuzuDB User Defined Functions (UDF).

## Problem Statement

In an append-only graph system where priorities change over time:
- New requirements should be able to take higher priority than existing ones
- Priorities need to be unique within a project
- We need to recalculate/redistribute priority values (0-255 range using UINT8)
- Batch updates of all nodes may be necessary

## Solution Approach

Using KuzuDB UDF to implement priority recalculation algorithms that can:
1. Redistribute priorities to maintain uniqueness
2. Compress existing priorities when inserting new high-priority items
3. Normalize priorities to fit within UINT8 range (0-255)

## Setup

```bash
cd /home/nixos/bin/src/poc/priority_recalculation
nix-shell
uv venv
uv pip install -e .
```

## Running Tests

```bash
# Run unified TDD tests (Red→Green progression + 異常系)
uv run pytest test_priority_tdd_unified.py -v

# Run demonstration
uv run python demo_priority_recalculation.py

# Run module with examples
uv run python mod.py
```

## Key Features

- Priority redistribution function
- Priority compression for new inserts
- Batch priority normalization
- Performance comparison between Cypher and UDF approaches

## Implementation Details

### UDF Functions

1. **calc_redistributed_priority(current, index, total)**: Redistributes priorities evenly across 0-255
2. **calc_compressed_priority(current, factor)**: Compresses priority by a factor (0-1)
3. **calc_normalized_priority(current, min, max, target_min, target_max)**: Normalizes to target range
4. **find_gap_position(target, priorities_str)**: Finds optimal insertion position
5. **rebalance_status()**: Returns rebalancing status

### Key Design Decisions

- Used UINT8 (0-255) for priority values to maximize unique positions
- Implemented scalar UDFs instead of complex list operations due to KuzuDB limitations
- Manual index calculation for redistribution to avoid unsupported window functions
- String-based priority list passing for gap finding function

## Advanced Test Scenarios (TDD Red)

The test suite includes realistic scenarios that require advanced UDF implementations:

### 1. **Insertion After Redistribution**
- Scenario: Adding priority=200 to an already evenly distributed set (0, 63, 127, 191, 255)
- Challenge: Maintaining distribution balance while inserting

### 2. **Priority Collisions**
- Scenario: Adding a requirement with the same priority as an existing one
- Challenge: Resolving conflicts while maintaining uniqueness

### 3. **Max Priority Conflicts** 
- Scenario: Multiple "most urgent" items (priority=255) competing
- Real-world case: When stakeholders keep saying "this is THE most important"

### 4. **Priority Escalation**
- Scenario: Tightly packed high priorities (240-255) need rebalancing
- Challenge: Making room in a crowded priority range

### 5. **Batch Insertions**
- Scenario: Multiple requirements added simultaneously, some with duplicate priorities
- Challenge: Atomic operation maintaining global uniqueness