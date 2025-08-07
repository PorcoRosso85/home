#!/usr/bin/env bash
#
# Email Archive POC - Local Testing Script
# Demonstrates the complete email archiving workflow from start to finish
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MINIO_PORT="9000"
MINIO_CONSOLE_PORT="9001"
BUCKET_NAME="email-archive"
ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"

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
    echo "║        Demonstrating Full Email Archiving Workflow          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
}

check_prerequisites() {
    log_step "1. Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_DIR/package.json" ] || [ ! -f "$PROJECT_DIR/src/index.js" ]; then
        log_error "Not in the correct project directory. Expected to find package.json and src/index.js"
        exit 1
    fi
    
    # Check required tools
    local missing_tools=()
    
    if ! command -v minio &> /dev/null; then
        missing_tools+=("minio")
    fi
    
    if ! command -v mc &> /dev/null; then
        missing_tools+=("mc (MinIO client)")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Run 'nix develop' to enter the development shell with all dependencies"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

ensure_minio_running() {
    log_step "2. Ensuring MinIO is running..."
    
    # Check if MinIO is already running
    if curl -s "http://localhost:$MINIO_PORT/minio/health/live" &>/dev/null; then
        log_success "MinIO is already running"
        return 0
    fi
    
    log_info "Starting MinIO server..."
    cd "$PROJECT_DIR"
    
    # Start MinIO using the setup script
    ./setup-minio.sh --keep-running &
    SETUP_PID=$!
    
    log_info "Waiting for MinIO to be ready..."
    
    # Wait for MinIO to be ready (max 30 seconds)
    for i in {1..30}; do
        if curl -s "http://localhost:$MINIO_PORT/minio/health/live" &>/dev/null; then
            log_success "MinIO is now running and ready"
            return 0
        fi
        sleep 1
    done
    
    log_error "MinIO failed to start within 30 seconds"
    exit 1
}

send_test_email() {
    log_step "3. Sending test email through Worker..."
    
    cd "$PROJECT_DIR"
    
    # Create a test email message
    local test_email_id="demo-$(date +%s)@example.com"
    local test_subject="Email Archive Demo - $(date '+%Y-%m-%d %H:%M:%S')"
    
    cat > /tmp/test_email.eml << EOF
Message-ID: <${test_email_id}>
From: demo-sender@example.com
To: demo-recipient@yourdomain.com
Subject: ${test_subject}
Date: $(date -R)
Content-Type: text/plain; charset=utf-8

This is a demonstration email for the Email Archive POC.

Generated at: $(date '+%Y-%m-%d %H:%M:%S %Z')
Test ID: ${test_email_id}

This email demonstrates:
- Automatic archiving to MinIO S3 storage
- Hierarchical organization by date
- Metadata extraction and storage
- Local email preservation

The system successfully:
✓ Received the email
✓ Parsed headers and content
✓ Generated storage path
✓ Saved to S3-compatible storage
✓ Created searchable metadata

Archive location: emails/$(date +%Y/%m/%d)/${test_email_id}
EOF
    
    log_info "Created test email with ID: $test_email_id"
    
    # Process the email through the Worker
    log_info "Processing email through Worker..."
    
    # Use the integration test infrastructure to simulate email processing
    node -e "
        import('./test/integration_test.js').then(async (module) => {
            const IntegrationTestSuite = module.default;
            const testSuite = new IntegrationTestSuite();
            
            // Load the worker module
            await testSuite.loadWorkerModule();
            
            // Read the test email
            const fs = await import('fs/promises');
            const rawEmail = await fs.readFile('/tmp/test_email.eml', 'utf-8');
            
            // Create mock message
            const mockMessage = testSuite.createMockMessage(
                rawEmail, 
                'demo-sender@example.com', 
                ['demo-recipient@yourdomain.com']
            );
            
            // Create mock environment
            const mockEnv = testSuite.createMockEnv();
            
            // Process the email
            const response = await testSuite.workerModule.default.email(mockMessage, mockEnv, {});
            
            console.log('Worker Response Status:', response.status);
            console.log('Worker Response:', await response.text());
            
            if (response.status === 200) {
                console.log('✅ Email processed successfully by Worker');
            } else {
                console.log('❌ Email processing failed');
                process.exit(1);
            }
        }).catch(error => {
            console.error('Error:', error.message);
            process.exit(1);
        });
    "
    
    if [ $? -eq 0 ]; then
        log_success "Email sent and processed successfully"
        echo "TEST_EMAIL_ID=$test_email_id" > /tmp/demo_vars.env
    else
        log_error "Failed to process email through Worker"
        exit 1
    fi
}

verify_archival() {
    log_step "4. Verifying email was archived correctly..."
    
    # Source the test email ID
    source /tmp/demo_vars.env
    
    local today_path="emails/$(date +%Y/%m/%d)"
    local email_key="${today_path}/${TEST_EMAIL_ID}"
    
    log_info "Looking for archived files at: $email_key"
    
    # Configure MinIO client
    mc alias set local "http://localhost:$MINIO_PORT" "$ACCESS_KEY" "$SECRET_KEY" &>/dev/null
    
    # Check if files exist
    local eml_exists=false
    local json_exists=false
    
    if mc stat "local/$BUCKET_NAME/${email_key}.eml" &>/dev/null; then
        eml_exists=true
        log_success "✓ EML file found: ${email_key}.eml"
    else
        log_warning "✗ EML file not found: ${email_key}.eml"
    fi
    
    if mc stat "local/$BUCKET_NAME/${email_key}.json" &>/dev/null; then
        json_exists=true
        log_success "✓ JSON metadata found: ${email_key}.json"
    else
        log_warning "✗ JSON metadata not found: ${email_key}.json"
    fi
    
    if [ "$eml_exists" = true ] && [ "$json_exists" = true ]; then
        log_success "Email archived successfully!"
        return 0
    else
        log_error "Email archival verification failed"
        
        # Show what files do exist
        log_info "Available files in bucket:"
        mc ls "local/$BUCKET_NAME/$today_path" --recursive || echo "No files found in today's path"
        
        return 1
    fi
}

display_archived_files() {
    log_step "5. Displaying archived files..."
    
    # Source the test email ID
    source /tmp/demo_vars.env
    
    local today_path="emails/$(date +%Y/%m/%d)"
    local email_key="${today_path}/${TEST_EMAIL_ID}"
    
    echo
    echo "═══════════════════════════════════════════════════════════════"
    echo "                        ARCHIVED EMAIL                        "
    echo "═══════════════════════════════════════════════════════════════"
    echo
    
    # Display the raw email content
    echo -e "${CYAN}📧 Raw Email Content (.eml file):${NC}"
    echo "-------------------------------------------------------------------"
    mc cat "local/$BUCKET_NAME/${email_key}.eml" 2>/dev/null || echo "Could not retrieve EML file"
    echo
    
    # Display the metadata
    echo -e "${CYAN}📋 Email Metadata (.json file):${NC}"
    echo "-------------------------------------------------------------------"
    mc cat "local/$BUCKET_NAME/${email_key}.json" 2>/dev/null | node -e "
        let input = '';
        process.stdin.on('data', chunk => input += chunk);
        process.stdin.on('end', () => {
            try {
                const metadata = JSON.parse(input);
                console.log(JSON.stringify(metadata, null, 2));
            } catch (e) {
                console.log(input);
            }
        });
    " || echo "Could not retrieve JSON metadata"
    echo
    
    # Show file information
    echo -e "${CYAN}📁 File Information:${NC}"
    echo "-------------------------------------------------------------------"
    echo "Storage Path: $email_key"
    echo "EML File Size: $(mc stat "local/$BUCKET_NAME/${email_key}.eml" 2>/dev/null | grep 'Size' | awk '{print $2}' || echo 'Unknown') bytes"
    echo "JSON File Size: $(mc stat "local/$BUCKET_NAME/${email_key}.json" 2>/dev/null | grep 'Size' | awk '{print $2}' || echo 'Unknown') bytes"
    echo "Archive Date: $(date)"
    echo
}

show_system_status() {
    log_step "6. System Status Summary..."
    
    echo
    echo "═══════════════════════════════════════════════════════════════"
    echo "                      SYSTEM STATUS                           "
    echo "═══════════════════════════════════════════════════════════════"
    echo
    
    # MinIO status
    echo -e "${CYAN}🗄️  MinIO Server Status:${NC}"
    if curl -s "http://localhost:$MINIO_PORT/minio/health/live" &>/dev/null; then
        echo "  ✅ Running on http://localhost:$MINIO_PORT"
        echo "  🎛️  Console: http://localhost:$MINIO_CONSOLE_PORT"
        echo "  🔑 Access Key: $ACCESS_KEY"
        echo "  🗝️  Secret Key: $SECRET_KEY"
    else
        echo "  ❌ Not running"
    fi
    echo
    
    # Bucket status
    echo -e "${CYAN}🪣 Bucket Status:${NC}"
    local total_objects=$(mc ls "local/$BUCKET_NAME" --recursive 2>/dev/null | wc -l || echo "0")
    echo "  📦 Bucket: $BUCKET_NAME"
    echo "  📁 Total objects: $total_objects"
    echo "  📅 Today's emails: $(mc ls "local/$BUCKET_NAME/emails/$(date +%Y/%m/%d)" --recursive 2>/dev/null | wc -l || echo "0")"
    echo
    
    # Worker status
    echo -e "${CYAN}⚙️  Worker Status:${NC}"
    if [ -f "$PROJECT_DIR/src/index.js" ]; then
        echo "  ✅ Worker code available"
        echo "  📝 Version: $(grep -o '"workerVersion": "[^"]*"' "$PROJECT_DIR/src/index.js" | cut -d'"' -f4 || echo 'Unknown')"
    else
        echo "  ❌ Worker code not found"
    fi
    echo
    
    # Recent emails
    echo -e "${CYAN}📬 Recent Archived Emails:${NC}"
    mc ls "local/$BUCKET_NAME/emails/$(date +%Y/%m/%d)" --recursive 2>/dev/null | tail -10 || echo "  No emails found for today"
    echo
}

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f /tmp/test_email.eml /tmp/demo_vars.env
}

print_next_steps() {
    echo
    echo "═══════════════════════════════════════════════════════════════"
    echo "                        NEXT STEPS                            "
    echo "═══════════════════════════════════════════════════════════════"
    echo
    echo -e "${GREEN}✅ Email Archive Demo Completed Successfully!${NC}"
    echo
    echo "What happened:"
    echo "  1. ✓ MinIO S3-compatible storage was started"
    echo "  2. ✓ A test email was created and processed"
    echo "  3. ✓ The Worker parsed and archived the email"
    echo "  4. ✓ Files were stored in hierarchical structure"
    echo "  5. ✓ Metadata was extracted and saved as JSON"
    echo
    echo "Available actions:"
    echo "  🎛️  View MinIO Console:     http://localhost:$MINIO_CONSOLE_PORT"
    echo "  🧪 Run integration tests:  node test/integration_test.js"
    echo "  🔍 List all archived emails: mc ls local/$BUCKET_NAME --recursive"
    echo "  🛑 Stop MinIO server:      kill \$(cat $PROJECT_DIR/.minio.pid) && rm $PROJECT_DIR/.minio.pid"
    echo
    echo "To test with real emails:"
    echo "  1. Configure Cloudflare Email Routing"
    echo "  2. Deploy the Worker to Cloudflare"
    echo "  3. Set up environment variables"
    echo "  4. Send emails to your configured domain"
    echo
}

main() {
    print_banner
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    # Run the demo steps
    check_prerequisites
    ensure_minio_running
    send_test_email
    
    if verify_archival; then
        display_archived_files
        show_system_status
        print_next_steps
        exit 0
    else
        log_error "Demo failed during verification step"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Email Archive POC - Local Testing Script"
        echo "Usage: $0 [--help]"
        echo ""
        echo "This script demonstrates the complete email archiving workflow:"
        echo "  1. Starts MinIO if not running"
        echo "  2. Creates and sends a test email through the Worker"
        echo "  3. Verifies the email was archived correctly"
        echo "  4. Displays the archived files and system status"
        echo ""
        echo "Options:"
        echo "  --help           Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac