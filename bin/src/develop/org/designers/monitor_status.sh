#!/bin/bash
# Monitor the status of all designers

echo "=== Manager Task Status ==="
echo ""

for mgr in x y z; do
    echo "Manager $mgr:"
    
    # Count tasks by status
    TODO_COUNT=$(grep "^\[TODO\]" "designers/$mgr/instructions.md" 2>/dev/null | wc -l)
    WIP_COUNT=$(grep "^\[WIP\]" "designers/$mgr/instructions.md" 2>/dev/null | wc -l)
    DONE_COUNT=$(grep "^\[DONE\]" "designers/$mgr/instructions.md" 2>/dev/null | wc -l)
    BLOCKED_COUNT=$(grep "^\[BLOCKED\]" "designers/$mgr/instructions.md" 2>/dev/null | wc -l)
    
    echo "  TODO: $TODO_COUNT | WIP: $WIP_COUNT | DONE: $DONE_COUNT | BLOCKED: $BLOCKED_COUNT"
    
    # Show current WIP task
    if [ "$WIP_COUNT" -gt 0 ]; then
        WIP_TASK=$(grep "^\[WIP\]" "designers/$mgr/instructions.md" | head -1)
        echo "  Working on: $WIP_TASK"
    fi
    
    # Check last status update
    if [ -f "designers/$mgr/status.md" ]; then
        LAST_LOG=$(tail -1 "designers/$mgr/status.md" | grep -E "^\[")
        if [ ! -z "$LAST_LOG" ]; then
            echo "  Last update: $LAST_LOG"
        fi
    fi
    
    echo ""
done

echo "=== Summary ==="
TOTAL_TODO=$(grep -c "^\[TODO\]" designers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
TOTAL_WIP=$(grep -c "^\[WIP\]" designers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
TOTAL_DONE=$(grep -c "^\[DONE\]" designers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Total: TODO=$TOTAL_TODO, WIP=$TOTAL_WIP, DONE=$TOTAL_DONE"