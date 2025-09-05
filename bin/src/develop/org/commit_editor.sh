#!/usr/bin/env bash

# /commit command editor for orchestrator
# Purpose: Help orchestrator identify and commit only Claude-edited files

set -euo pipefail

echo "=== Git Commit Editor for Orchestrator ==="
echo ""

# 1. Show current status
echo "📊 Current git status:"
git status --short

echo ""
echo "📝 Analyzing edited files..."

# 2. Identify Claude-edited files
CLAUDE_FILES=()
OTHER_FILES=()

# Check each modified file
while IFS= read -r line; do
    status=$(echo "$line" | cut -c1-2)
    file=$(echo "$line" | cut -c4-)
    
    # Skip deleted files
    if [[ "$status" == " D" ]] || [[ "$status" == "D " ]]; then
        continue
    fi
    
    # Check if file is in current directory
    if [[ "$file" == *".."* ]]; then
        continue
    fi
    
    # Categorize files
    case "$file" in
        managers/*/status.md|managers/*/instructions.md)
            echo "  🤖 Manager file: $file"
            OTHER_FILES+=("$file")
            ;;
        *.jsonl)
            echo "  📊 Session tracking: $file"
            OTHER_FILES+=("$file")
            ;;
        *)
            # Check git log to see who last edited
            if git log -1 --format="%s" -- "$file" 2>/dev/null | grep -q "Claude"; then
                echo "  ✅ Claude-edited: $file"
                CLAUDE_FILES+=("$file")
            else
                echo "  👥 Other editor: $file"
                OTHER_FILES+=("$file")
            fi
            ;;
    esac
done < <(git status --short)

echo ""
echo "=== Summary ==="
echo "Claude-edited files: ${#CLAUDE_FILES[@]}"
echo "Other files: ${#OTHER_FILES[@]}"

# 3. If no Claude files, exit
if [ ${#CLAUDE_FILES[@]} -eq 0 ]; then
    echo ""
    echo "❌ No files edited by Claude in this session."
    echo "   Orchestrator delegates work to Managers."
    exit 0
fi

# 4. Stage only Claude files
echo ""
echo "📦 Staging Claude-edited files..."
git reset HEAD 2>/dev/null || true

for file in "${CLAUDE_FILES[@]}"; do
    echo "  Adding: $file"
    git add "$file"
done

# 5. Show staged files
echo ""
echo "✅ Staged files:"
git status --short --branch | grep '^[AM]'

# 6. Create commit
echo ""
read -p "Enter commit message (or 'skip' to cancel): " commit_msg

if [ "$commit_msg" == "skip" ]; then
    echo "Commit cancelled."
    git reset HEAD
    exit 0
fi

# Create full commit message with Claude signature
full_msg="$commit_msg

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "$full_msg"

echo ""
echo "✅ Commit successful!"

# 7. Check remaining files
echo ""
echo "📋 Remaining uncommitted files in current directory:"
git status . --short

echo ""
echo "=== Explanation of uncommitted files ==="
for file in "${OTHER_FILES[@]}"; do
    case "$file" in
        managers/*/status.md)
            echo "  $file → Manager work log (not orchestrator's edit)"
            ;;
        managers/*/instructions.md)
            echo "  $file → Manager task list (managed by Manager)"
            ;;
        *.jsonl)
            echo "  $file → Automatic session tracking"
            ;;
        *)
            echo "  $file → Modified by other developer/tool"
            ;;
    esac
done

echo ""
echo "Done!"