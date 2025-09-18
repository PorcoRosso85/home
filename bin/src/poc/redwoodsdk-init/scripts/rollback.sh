#!/bin/bash

# Cloudflare Workers rollback script
set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Parse arguments
VERSION_TAG="${1:-}"
DRY_RUN="${2:-false}"

# Banner
print_color $BLUE "╔════════════════════════════════════════════╗"
print_color $BLUE "║   🔄 Cloudflare Workers Rollback           ║"
print_color $BLUE "╚════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

# Get project name from wrangler.jsonc
PROJECT_NAME=$(grep '"name"' wrangler.jsonc | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_NAME" ]; then
    print_color $RED "❌ Could not determine project name from wrangler.jsonc"
    exit 1
fi

print_color $NC "Project: $YELLOW$PROJECT_NAME$NC"
echo ""

# Function to list available versions
list_versions() {
    print_color $YELLOW "📋 Available versions:"
    
    # Try to list deployments
    if npx wrangler deployments list &> /tmp/deployments.log; then
        cat /tmp/deployments.log | tail -n +2 | head -10
    else
        print_color $RED "❌ Failed to list deployments"
        print_color $YELLOW "Make sure you're authenticated: wrangler login"
        exit 1
    fi
}

# Function to get current version
get_current_version() {
    # Get current deployment ID
    CURRENT=$(npx wrangler deployments list 2>/dev/null | grep "Current" | awk '{print $1}')
    echo "$CURRENT"
}

# Function to perform rollback
perform_rollback() {
    local target_version=$1
    
    if [ "$DRY_RUN" = "true" ]; then
        print_color $YELLOW "🔍 DRY RUN - Would rollback to version: $target_version"
        return 0
    fi
    
    print_color $YELLOW "🔄 Rolling back to version: $target_version"
    
    # Perform the rollback
    if npx wrangler rollback "$target_version" --message "Rollback via script"; then
        print_color $GREEN "✅ Rollback successful!"
        return 0
    else
        print_color $RED "❌ Rollback failed!"
        return 1
    fi
}

# Main logic
if [ -z "$VERSION_TAG" ]; then
    # Interactive mode
    print_color $YELLOW "No version specified. Entering interactive mode..."
    echo ""
    
    # Show current version
    CURRENT_VERSION=$(get_current_version)
    if [ -n "$CURRENT_VERSION" ]; then
        print_color $GREEN "Current version: $CURRENT_VERSION"
        echo ""
    fi
    
    # List available versions
    list_versions
    echo ""
    
    # Prompt for version
    print_color $YELLOW "Enter the deployment ID to rollback to (or 'exit' to cancel):"
    read -r VERSION_TAG
    
    if [ "$VERSION_TAG" = "exit" ] || [ -z "$VERSION_TAG" ]; then
        print_color $YELLOW "Rollback cancelled."
        exit 0
    fi
fi

# Confirm rollback
print_color $YELLOW "⚠️  WARNING: You are about to rollback to version: $VERSION_TAG"
print_color $NC "This will:"
print_color $NC "  • Immediately switch production traffic"
print_color $NC "  • Revert all code changes since that version"
print_color $NC "  • Not affect database state"
echo ""

if [ "$DRY_RUN" != "true" ]; then
    print_color $YELLOW "Are you sure? (yes/no):"
    read -r CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_color $YELLOW "Rollback cancelled."
        exit 0
    fi
fi

# Perform rollback
echo ""
perform_rollback "$VERSION_TAG"
ROLLBACK_STATUS=$?

if [ $ROLLBACK_STATUS -eq 0 ]; then
    echo ""
    print_color $BLUE "╔════════════════════════════════════════════╗"
    print_color $BLUE "║   ✅ Rollback Complete                     ║"
    print_color $BLUE "╚════════════════════════════════════════════╝"
    echo ""
    
    print_color $GREEN "Next steps:"
    print_color $NC "  1. Verify the application is working"
    print_color $NC "  2. Check error logs: wrangler tail"
    print_color $NC "  3. Monitor metrics in Cloudflare dashboard"
    print_color $NC "  4. Investigate the issue that caused the rollback"
    echo ""
    
    # Show new current version
    NEW_CURRENT=$(get_current_version)
    if [ -n "$NEW_CURRENT" ]; then
        print_color $GREEN "New current version: $NEW_CURRENT"
    fi
else
    echo ""
    print_color $RED "Rollback failed. Please check:"
    print_color $NC "  • Authentication: wrangler login"
    print_color $NC "  • Version ID is valid"
    print_color $NC "  • Network connectivity"
    exit 1
fi