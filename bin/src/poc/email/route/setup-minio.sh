#!/usr/bin/env bash
#
# MinIO Setup Script for Email Archive POC
# Initializes MinIO server with email-archive bucket and proper configuration
#

set -euo pipefail

# Configuration
MINIO_DATA_DIR="./minio-data"
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

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v minio &> /dev/null; then
        log_error "MinIO server not found. Please ensure it's installed via Nix."
        exit 1
    fi
    
    if ! command -v mc &> /dev/null; then
        log_error "MinIO client (mc) not found. Please ensure it's installed via Nix."
        exit 1
    fi
    
    log_success "All dependencies found"
}

setup_data_directory() {
    log_info "Setting up data directory..."
    
    if [ ! -d "$MINIO_DATA_DIR" ]; then
        mkdir -p "$MINIO_DATA_DIR"
        log_success "Created data directory: $MINIO_DATA_DIR"
    else
        log_info "Data directory already exists: $MINIO_DATA_DIR"
    fi
}

start_minio_background() {
    log_info "Starting MinIO server..."
    
    # Check if MinIO is already running
    if curl -s "http://localhost:$MINIO_PORT/minio/health/live" &>/dev/null; then
        log_warning "MinIO appears to be already running on port $MINIO_PORT"
        return 0
    fi
    
    # Start MinIO in background
    MINIO_ROOT_USER="$ACCESS_KEY" \
    MINIO_ROOT_PASSWORD="$SECRET_KEY" \
    minio server \
        --address ":$MINIO_PORT" \
        --console-address ":$MINIO_CONSOLE_PORT" \
        "$MINIO_DATA_DIR" &
    
    MINIO_PID=$!
    echo $MINIO_PID > .minio.pid
    
    log_info "MinIO started with PID: $MINIO_PID"
    log_info "Waiting for MinIO to be ready..."
    
    # Wait for MinIO to be ready (max 30 seconds)
    for i in {1..30}; do
        if curl -s "http://localhost:$MINIO_PORT/minio/health/live" &>/dev/null; then
            log_success "MinIO is ready!"
            return 0
        fi
        sleep 1
    done
    
    log_error "MinIO failed to start within 30 seconds"
    exit 1
}

configure_client() {
    log_info "Configuring MinIO client..."
    
    # Configure mc client
    mc alias set local "http://localhost:$MINIO_PORT" "$ACCESS_KEY" "$SECRET_KEY" 2>/dev/null || {
        log_error "Failed to configure MinIO client"
        exit 1
    }
    
    log_success "MinIO client configured"
}

create_bucket() {
    log_info "Creating email-archive bucket..."
    
    # Create bucket if it doesn't exist
    if mc ls local/"$BUCKET_NAME" &>/dev/null; then
        log_warning "Bucket '$BUCKET_NAME' already exists"
    else
        mc mb local/"$BUCKET_NAME" || {
            log_error "Failed to create bucket '$BUCKET_NAME'"
            exit 1
        }
        log_success "Bucket '$BUCKET_NAME' created"
    fi
}

setup_bucket_policy() {
    log_info "Setting up bucket policy..."
    
    # Create temporary policy file
    POLICY_FILE=$(mktemp)
    cat > "$POLICY_FILE" << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}/*"]
    },
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}"]
    }
  ]
}
EOF
    
    # Apply policy
    mc anonymous set-json "$POLICY_FILE" local/"$BUCKET_NAME" || {
        log_warning "Failed to set bucket policy (this may be OK for development)"
    }
    
    rm "$POLICY_FILE"
    log_success "Bucket policy configured"
}

create_test_structure() {
    log_info "Creating test directory structure..."
    
    # Create test email structure
    TEST_DATE=$(date +%Y/%m/%d)
    TEST_KEY="emails/$TEST_DATE/test-setup-$(date +%s)@example.com"
    
    # Create test metadata
    TEST_METADATA=$(cat << EOF
{
  "messageId": "test-setup-$(date +%s)@example.com",
  "from": "setup@example.com",
  "to": ["test@example.com"],
  "subject": "Test Setup Email",
  "receivedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "size": 142,
  "setup": true
}
EOF
)
    
    # Upload test metadata
    echo "$TEST_METADATA" | mc pipe local/"$BUCKET_NAME"/"$TEST_KEY".json || {
        log_warning "Failed to create test structure"
        return 1
    }
    
    log_success "Test directory structure created: $TEST_KEY"
}

show_status() {
    log_info "MinIO setup complete!"
    echo
    echo "=== MinIO Configuration ==="
    echo "Server URL:      http://localhost:$MINIO_PORT"
    echo "Console URL:     http://localhost:$MINIO_CONSOLE_PORT"
    echo "Access Key:      $ACCESS_KEY"
    echo "Secret Key:      $SECRET_KEY"
    echo "Bucket Name:     $BUCKET_NAME"
    echo "Data Directory:  $MINIO_DATA_DIR"
    echo
    echo "=== Bucket Contents ==="
    mc ls local/"$BUCKET_NAME" --recursive || echo "Bucket is empty"
    echo
    echo "=== Next Steps ==="
    echo "1. Visit the console: http://localhost:$MINIO_CONSOLE_PORT"
    echo "2. Configure your Worker with these credentials"
    echo "3. Test email archiving: nix run .#test-archive"
    echo "4. Stop MinIO: kill \$(cat .minio.pid) && rm .minio.pid"
    echo
}

cleanup_on_exit() {
    if [ -f .minio.pid ]; then
        PID=$(cat .minio.pid)
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Cleaning up MinIO process..."
            kill "$PID"
            rm .minio.pid
        fi
    fi
}

main() {
    log_info "Starting MinIO setup for Email Archive POC"
    
    # Set up cleanup on exit
    trap cleanup_on_exit EXIT
    
    check_dependencies
    setup_data_directory
    start_minio_background
    configure_client
    create_bucket
    setup_bucket_policy
    create_test_structure
    show_status
    
    # Keep MinIO running if requested
    if [ "${1:-}" = "--keep-running" ]; then
        log_info "MinIO will keep running. Use Ctrl+C to stop."
        wait
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--keep-running] [--help]"
        echo ""
        echo "Options:"
        echo "  --keep-running    Keep MinIO running after setup"
        echo "  --help           Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac