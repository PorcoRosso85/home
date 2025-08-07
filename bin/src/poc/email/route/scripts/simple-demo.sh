#!/usr/bin/env bash
#
# Email Archive POC - Simple Demonstration
# Shows the system architecture and demonstrates key components
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_banner() {
    echo
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Email Archive POC Demo                      ║"
    echo "║            Simple Architecture Demonstration                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
}

show_architecture() {
    log_step "1. System Architecture Overview"
    echo
    echo "Email Archiving Flow:"
    echo "┌─────────────┐    ┌──────────────────┐    ┌─────────┐    ┌──────────┐"
    echo "│  外部送信者  │───>│ Cloudflare Email │───>│ Worker  │───>│  MinIO   │"
    echo "│   Sender    │    │    Routing       │    │ Archive │    │   S3     │"
    echo "└─────────────┘    └──────────────────┘    └─────────┘    └──────────┘"
    echo "                            │                                   ↑"
    echo "                            ▼                                   │"
    echo "                   ┌──────────────────┐                        │"
    echo "                   │  Normal Inbox    │                        │"
    echo "                   │  (Gmail, etc.)   │                        │"
    echo "                   └──────────────────┘                    Local Storage"
    echo
    log_success "Architecture: Cloudflare Worker captures all emails and stores them locally"
    echo
}

show_components() {
    log_step "2. System Components"
    echo
    
    # Worker Component
    echo -e "${CYAN}📦 Email Worker (Cloudflare):${NC}"
    echo "  Location: src/index.js"
    echo "  Purpose: Intercepts incoming emails, extracts metadata, archives to S3"
    echo "  Features:"
    echo "    ✓ Raw email preservation (.eml format)"
    echo "    ✓ Metadata extraction and storage (.json format)"
    echo "    ✓ Hierarchical organization by date"
    echo "    ✓ S3-compatible storage integration"
    echo "    ✓ Error handling and logging"
    echo
    
    # MinIO Component
    echo -e "${CYAN}🗄️  MinIO Storage (Local S3):${NC}"
    echo "  Purpose: S3-compatible object storage for email archives"
    echo "  Features:"
    echo "    ✓ RESTful API compatible with AWS S3"
    echo "    ✓ Web console for management"
    echo "    ✓ Bucket policies and access control"
    echo "    ✓ Hierarchical object organization"
    echo
    
    # Configuration
    echo -e "${CYAN}⚙️  Configuration:${NC}"
    echo "  Environment Variables:"
    echo "    - MINIO_ENDPOINT: http://localhost:9000"
    echo "    - MINIO_ACCESS_KEY: minioadmin"
    echo "    - MINIO_SECRET_KEY: minioadmin"
    echo "    - BUCKET_NAME: email-archive"
    echo
}

examine_worker_code() {
    log_step "3. Email Worker Implementation"
    echo
    
    echo -e "${CYAN}📄 Worker Code Structure:${NC}"
    echo "-------------------------------------------------------------------"
    
    if [ -f "$PROJECT_DIR/src/index.js" ]; then
        echo "✅ Worker implementation found at src/index.js"
        echo
        echo "Key functions:"
        grep -n "async function\|function\|async email" "$PROJECT_DIR/src/index.js" | head -10 | while IFS= read -r line; do
            echo "  $line"
        done
        echo
        echo "Main workflow steps:"
        echo "  1. 📧 Receive email via Cloudflare Email Routing"
        echo "  2. 📝 Extract raw email content and headers"
        echo "  3. 🏷️  Generate comprehensive metadata"
        echo "  4. 📁 Create hierarchical storage path (emails/YYYY/MM/DD/messageId)"
        echo "  5. 💾 Store both .eml (raw) and .json (metadata) files"
        echo "  6. ✅ Return success response"
    else
        log_error "Worker implementation not found"
    fi
    echo
}

show_storage_structure() {
    log_step "4. Storage Organization"
    echo
    
    echo -e "${CYAN}📁 Email Archive Structure:${NC}"
    echo "-------------------------------------------------------------------"
    echo "email-archive/                    <- S3 Bucket"
    echo "└── emails/"
    echo "    └── 2025/"
    echo "        └── 08/"
    echo "            └── 05/"
    echo "                ├── message-123@example.com.eml     <- Raw email"
    echo "                ├── message-123@example.com.json    <- Metadata"
    echo "                ├── message-456@example.com.eml"
    echo "                └── message-456@example.com.json"
    echo
    
    if [ -d "$PROJECT_DIR/minio-data/email-archive/emails" ]; then
        echo -e "${CYAN}📊 Current Archive Contents:${NC}"
        echo "-------------------------------------------------------------------"
        find "$PROJECT_DIR/minio-data/email-archive/emails" -type f 2>/dev/null | head -20 | while IFS= read -r file; do
            # Extract relative path from minio-data
            rel_path=${file#$PROJECT_DIR/minio-data/email-archive/}
            echo "  📄 $rel_path"
        done
        
        total_files=$(find "$PROJECT_DIR/minio-data/email-archive/emails" -type f 2>/dev/null | wc -l)
        echo "  📈 Total archived files: $total_files"
    else
        echo "  📭 No archived emails found (MinIO not started or no emails processed)"
    fi
    echo
}

show_metadata_example() {
    log_step "5. Email Metadata Structure"
    echo
    
    echo -e "${CYAN}📋 Example Email Metadata (.json):${NC}"
    echo "-------------------------------------------------------------------"
    cat << 'EOF'
{
  "messageId": "simple-text-123@example.com",
  "originalMessageId": "<simple-text-123@example.com>",
  "receivedAt": "2025-08-05T19:30:45.123Z",
  "emailDate": "2025-08-05T19:30:00.000Z",
  "from": "sender@example.com",
  "to": ["recipient@yourdomain.com"],
  "subject": "Important Business Email",
  "size": 1024,
  "contentType": "text/plain; charset=utf-8",
  "isMultipart": false,
  "headers": {
    "message-id": "<simple-text-123@example.com>",
    "from": "sender@example.com",
    "to": "recipient@yourdomain.com",
    "subject": "Important Business Email",
    "date": "Mon, 05 Aug 2025 19:30:00 +0000",
    "content-type": "text/plain; charset=utf-8"
  },
  "archivedBy": "email-archive-worker",
  "workerVersion": "1.0.0"
}
EOF
    echo
    log_success "Metadata provides searchable, structured information about each email"
    echo
}

show_test_infrastructure() {
    log_step "6. Testing Infrastructure"
    echo
    
    echo -e "${CYAN}🧪 Available Tests:${NC}"
    echo "-------------------------------------------------------------------"
    
    if [ -f "$PROJECT_DIR/test/integration_test.js" ]; then
        echo "  ✅ integration_test.js - Full workflow testing"
        echo "     - Basic email archiving"
        echo "     - HTML emails with attachments"
        echo "     - Malformed email handling"
        echo "     - Storage key generation"
        echo "     - Concurrent processing"
    fi
    
    if [ -f "$PROJECT_DIR/setup-minio.sh" ]; then
        echo "  ✅ setup-minio.sh - MinIO server setup and configuration"
    fi
    
    if [ -f "$PROJECT_DIR/health-check.sh" ]; then
        echo "  ✅ health-check.sh - System health verification"
    fi
    
    echo
    echo -e "${CYAN}🎯 Test Fixtures:${NC}"
    if [ -d "$PROJECT_DIR/test/fixtures" ]; then
        ls "$PROJECT_DIR/test/fixtures/"*.eml 2>/dev/null | while IFS= read -r fixture; do
            filename=$(basename "$fixture")
            echo "  📧 $filename"
        done
    fi
    echo
}

show_deployment_info() {
    log_step "7. Deployment Information"
    echo
    
    echo -e "${CYAN}🚀 Deployment Options:${NC}"
    echo "-------------------------------------------------------------------"
    echo "  Development (Local):"
    echo "    1. nix develop                    # Enter development shell"
    echo "    2. ./setup-minio.sh --keep-running    # Start MinIO"
    echo "    3. node test/integration_test.js      # Run tests"
    echo
    echo "  Production (Cloudflare):"
    echo "    1. Configure Email Routing for your domain"
    echo "    2. Deploy Worker: wrangler deploy"
    echo "    3. Set secrets: wrangler secret put MINIO_ACCESS_KEY"
    echo "    4. Set secrets: wrangler secret put MINIO_SECRET_KEY"
    echo "    5. Configure MINIO_ENDPOINT and BUCKET_NAME variables"
    echo
    
    echo -e "${CYAN}🔧 Requirements:${NC}"
    echo "  - Cloudflare account with Email Routing enabled"
    echo "  - Custom domain configured for email"
    echo "  - MinIO server (local or cloud-hosted)"
    echo "  - Network connectivity between Worker and MinIO"
    echo
}

show_security_considerations() {
    log_step "8. Security & Privacy"
    echo
    
    echo -e "${CYAN}🔒 Security Features:${NC}"
    echo "-------------------------------------------------------------------"
    echo "  ✅ Local Data Control: All emails stored on your infrastructure"
    echo "  ✅ Access Control: MinIO bucket policies restrict access"
    echo "  ✅ Encrypted Storage: MinIO supports server-side encryption"
    echo "  ✅ Encrypted Transit: HTTPS/TLS for all communications"
    echo "  ✅ No Third-party Storage: Zero dependency on external services"
    echo
    echo -e "${CYAN}⚠️  Important Considerations:${NC}"
    echo "  • Email content includes personal/sensitive information"
    echo "  • Implement proper backup and retention policies"
    echo "  • Consider encryption at rest for sensitive data"
    echo "  • Regular security audits of MinIO configuration"
    echo "  • Monitor access logs and implement alerting"
    echo
}

show_next_steps() {
    echo
    echo "═══════════════════════════════════════════════════════════════"
    echo "                        NEXT STEPS                            "
    echo "═══════════════════════════════════════════════════════════════"
    echo
    echo -e "${GREEN}✅ Email Archive POC Demonstration Complete!${NC}"
    echo
    echo "To run the full system:"
    echo "  1. 🏃 Start development environment: nix develop"
    echo "  2. 🗄️  Start MinIO server: ./setup-minio.sh --keep-running"
    echo "  3. 🧪 Run integration tests: node test/integration_test.js"
    echo "  4. 🎛️  View MinIO console: http://localhost:9001"
    echo
    echo "To deploy to production:"
    echo "  1. 🌐 Configure Cloudflare Email Routing"
    echo "  2. 🚀 Deploy Worker: wrangler deploy"
    echo "  3. 🔑 Configure secrets and environment variables"
    echo "  4. 📧 Test with real emails"
    echo
    echo "For more information:"
    echo "  📖 README.md - Detailed system documentation"
    echo "  📋 SETUP.md - Step-by-step setup instructions"
    echo "  ⚙️  WORKER_README.md - Worker-specific documentation"
    echo
}

main() {
    print_banner
    show_architecture
    show_components
    examine_worker_code
    show_storage_structure
    show_metadata_example
    show_test_infrastructure
    show_deployment_info
    show_security_considerations
    show_next_steps
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Email Archive POC - Simple Demonstration Script"
        echo "Usage: $0 [--help]"
        echo ""
        echo "This script provides an overview of the email archiving system"
        echo "without requiring a full development environment setup."
        echo ""
        echo "Options:"
        echo "  --help           Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac