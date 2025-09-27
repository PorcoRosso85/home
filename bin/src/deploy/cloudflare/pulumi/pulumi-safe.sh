#!/bin/bash
set -euo pipefail

# Pulumi Safe Operations Script
# Ensures preview-only mode and prevents accidental deployments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV="${1:-dev}"
ACTION="${2:-preview}"

echo "🛡️ Pulumi Safe Operations"
echo "========================"
echo "Environment: $ENV"
echo "Action: $ACTION"
echo ""

# Validate environment
case "$ENV" in
    "dev"|"stg"|"prod")
        echo "✅ Valid environment: $ENV"
        ;;
    *)
        echo "❌ Invalid environment: $ENV"
        echo "   Valid options: dev, stg, prod"
        exit 1
        ;;
esac

# Load environment variables if .env exists
if [[ -f .env ]]; then
    echo "📋 Loading environment variables from .env"
    set -a
    source .env
    set +a
else
    echo "⚠️ No .env file found. Using environment variables."
fi

# Validate required environment variables
if [[ -z "${CF_ACCOUNT_ID:-}" ]]; then
    echo "❌ CF_ACCOUNT_ID not set. Check your .env file."
    exit 1
fi

if [[ -z "${CF_API_TOKEN:-}" ]]; then
    echo "❌ CF_API_TOKEN not set. Check your .env file."
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Set Pulumi stack
echo "🔄 Selecting Pulumi stack: $ENV"
if ! pulumi stack select "$ENV" 2>/dev/null; then
    echo "📋 Stack $ENV not found. Creating..."
    pulumi stack init "$ENV"
    echo "✅ Stack $ENV created"
fi

# Perform action
case "$ACTION" in
    "preview")
        echo "👀 Running Pulumi preview for $ENV environment..."
        pulumi preview --stack "$ENV"
        ;;

    "validate")
        echo "🧪 Validating Pulumi configuration for $ENV environment..."
        pulumi config --stack "$ENV"
        pulumi preview --dry-run --stack "$ENV"
        echo "✅ Configuration validation completed"
        ;;

    "config")
        echo "📋 Showing configuration for $ENV environment..."
        pulumi config --stack "$ENV"
        ;;

    "up")
        echo "⚠️ WARNING: This is a PREVIEW-ONLY deployment!"
        echo "   No actual resources will be created/modified."
        echo "   This operation is safe for testing."
        echo ""
        read -p "Continue with preview deployment? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pulumi up --preview-only --stack "$ENV"
        else
            echo "❌ Deployment cancelled"
            exit 1
        fi
        ;;

    "destroy")
        echo "⚠️ WARNING: This is a PREVIEW-ONLY destruction!"
        echo "   No actual resources will be destroyed."
        echo "   This operation is safe for testing."
        echo ""
        read -p "Continue with preview destruction? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pulumi destroy --preview-only --stack "$ENV"
        else
            echo "❌ Destruction cancelled"
            exit 1
        fi
        ;;

    *)
        echo "❌ Unknown action: $ACTION"
        echo "Available actions:"
        echo "   preview   - Preview changes (safe)"
        echo "   validate  - Validate configuration (safe)"
        echo "   config    - Show stack configuration (safe)"
        echo "   up        - Deploy with preview-only (safe)"
        echo "   destroy   - Destroy with preview-only (safe)"
        echo ""
        echo "Usage: $0 [ENV] [ACTION]"
        echo "   ENV defaults to 'dev'"
        echo "   ACTION defaults to 'preview'"
        exit 1
        ;;
esac

echo ""
echo "🎉 Operation completed successfully!"