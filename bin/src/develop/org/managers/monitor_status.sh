#!/bin/bash
# Monitor the status of all managers

echo "=== Manager Task Status ==="
echo ""

for mgr in x y z; do
    echo "Manager $mgr:"
    
    # Count tasks by status
    TODO_COUNT=$(grep "^\[TODO\]" "managers/$mgr/instructions.md" 2>/dev/null | wc -l)
    WIP_COUNT=$(grep "^\[WIP\]" "managers/$mgr/instructions.md" 2>/dev/null | wc -l)
    DONE_COUNT=$(grep "^\[DONE\]" "managers/$mgr/instructions.md" 2>/dev/null | wc -l)
    BLOCKED_COUNT=$(grep "^\[BLOCKED\]" "managers/$mgr/instructions.md" 2>/dev/null | wc -l)
    
    echo "  TODO: $TODO_COUNT | WIP: $WIP_COUNT | DONE: $DONE_COUNT | BLOCKED: $BLOCKED_COUNT"
    
    # Show current WIP task
    if [ "$WIP_COUNT" -gt 0 ]; then
        WIP_TASK=$(grep "^\[WIP\]" "managers/$mgr/instructions.md" | head -1)
        echo "  Working on: $WIP_TASK"
    fi
    
    # Check last status update
    if [ -f "managers/$mgr/status.md" ]; then
        LAST_LOG=$(tail -1 "managers/$mgr/status.md" | grep -E "^\[")
        if [ ! -z "$LAST_LOG" ]; then
            echo "  Last update: $LAST_LOG"
        fi
    fi
    
    echo ""
done

echo "=== Summary ==="
TOTAL_TODO=$(grep -c "^\[TODO\]" managers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
TOTAL_WIP=$(grep -c "^\[WIP\]" managers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
TOTAL_DONE=$(grep -c "^\[DONE\]" managers/*/instructions.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Total: TODO=$TOTAL_TODO, WIP=$TOTAL_WIP, DONE=$TOTAL_DONE"