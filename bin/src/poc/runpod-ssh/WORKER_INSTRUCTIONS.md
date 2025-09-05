# RunPod SSH Flake - Worker Implementation Instructions

## Overview

This document provides detailed step-by-step instructions for Workers implementing the RunPod SSH Flake system. Each component should be implemented as a separate task with clear validation checkpoints.

## Prerequisites for All Workers

### Environment Setup
```bash
# Verify Nix flakes are enabled
nix --experimental-features 'nix-command flakes' --version

# Check required tools are available
command -v curl || echo "curl required"
command -v jq || echo "jq required"  
command -v ssh || echo "ssh required"
```

### Required Environment Variables
```bash
export RUNPOD_API_KEY="your_runpod_api_key"
export RUNPOD_API_URL="https://api.runpod.io/graphql"
export GITHUB_TOKEN="github_token_for_runner_registration"
```

## Component Implementation Instructions

## 1. RunPod Client (`runpod-client`)

### Responsibility
Execute GraphQL operations against RunPod API with proper error handling and response validation.

### Implementation Steps

#### Step 1.1: Create Base Structure
```bash
# Create component directory
mkdir -p components/runpod-client/{src,tests,docs}

# Create main executable
touch components/runpod-client/src/runpod-client
chmod +x components/runpod-client/src/runpod-client
```

#### Step 1.2: Implement Core GraphQL Function
Create `components/runpod-client/src/graphql.sh`:
```bash
#!/usr/bin/env bash
# Core GraphQL request function
# Input: query, variables (optional)
# Output: JSON response or error

graphql_request() {
    local query="$1"
    local variables="${2:-{}}"
    
    # Validation checkpoint
    [[ -z "$RUNPOD_API_KEY" ]] && { echo "ERROR: RUNPOD_API_KEY not set"; exit 1; }
    [[ -z "$query" ]] && { echo "ERROR: Query required"; exit 1; }
    
    # Execute request with error handling
    local response
    response=$(curl -s --fail-with-body \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        -d "{\"query\":\"$query\",\"variables\":$variables}" \
        "$RUNPOD_API_URL" 2>/dev/null)
    
    local curl_exit_code=$?
    
    # Error handling
    if [[ $curl_exit_code -ne 0 ]]; then
        echo "ERROR: Network request failed (exit code: $curl_exit_code)"
        exit 1
    fi
    
    # Validate JSON response
    if ! echo "$response" | jq . >/dev/null 2>&1; then
        echo "ERROR: Invalid JSON response"
        exit 1
    fi
    
    # Check for GraphQL errors
    local errors
    errors=$(echo "$response" | jq -r '.errors // empty')
    if [[ -n "$errors" ]]; then
        echo "ERROR: GraphQL errors detected: $errors"
        exit 1
    fi
    
    echo "$response"
}
```

#### Step 1.3: Implement Pod Operations
Create `components/runpod-client/src/operations.sh`:
```bash
#!/usr/bin/env bash
source "$(dirname "$0")/graphql.sh"

create_pod() {
    local image_name="$1"
    local gpu_type="$2"
    local gpu_count="${3:-1}"
    local bid_per_gpu="${4:-0.5}"
    
    local query='
    mutation createPod($input: PodRentInterruptableInput!) {
        podRentInterruptable(input: $input) {
            id
            desiredStatus
            imageName
            machineId
        }
    }'
    
    local variables=$(cat <<EOF
{
    "input": {
        "gpuCount": $gpu_count,
        "bidPerGpu": $bid_per_gpu,
        "gpuTypeId": "$gpu_type",
        "imageName": "$image_name",
        "minVcpuCount": 1,
        "minMemoryInGb": 4,
        "dockerArgs": "",
        "ports": "22/tcp",
        "volumeInGb": 50,
        "containerDiskInGb": 50,
        "startSSH": true
    }
}
EOF
)
    
    graphql_request "$query" "$variables"
}

get_pod() {
    local pod_id="$1"
    [[ -z "$pod_id" ]] && { echo "ERROR: Pod ID required"; exit 1; }
    
    local query='
    query getPod($podId: String!) {
        pod(input: {podId: $podId}) {
            id
            desiredStatus
            lastStatusChange
            imageName
            machineId
            machine {
                podHostId
            }
            runtime {
                uptimeInSeconds
                ports {
                    ip
                    isIpPublic
                    privatePort
                    publicPort
                }
            }
        }
    }'
    
    local variables="{\"podId\": \"$pod_id\"}"
    graphql_request "$query" "$variables"
}

# Additional operations: resume_pod, stop_pod, list_pods
```

#### Step 1.4: Create Main Executable
Update `components/runpod-client/src/runpod-client`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/operations.sh"

show_usage() {
    cat <<EOF
Usage: runpod-client <command> [options]

Commands:
    create <image> <gpu_type> [gpu_count] [bid_price]
    get <pod_id>
    resume <pod_id>  
    stop <pod_id>
    list [status]
    validate-auth

Options:
    --help, -h    Show this help message
    --verbose, -v Enable verbose output
EOF
}

case "${1:-}" in
    create)
        create_pod "${2:-}" "${3:-}" "${4:-1}" "${5:-0.5}"
        ;;
    get)
        get_pod "${2:-}"
        ;;
    # Add other cases...
    *)
        show_usage
        exit 1
        ;;
esac
```

### Testing Instructions for RunPod Client

#### Test 1.1: Authentication Validation
```bash
# Expected output: Valid JSON response or specific error
./components/runpod-client/src/runpod-client validate-auth

# Expected behavior: Should fail gracefully with invalid key
RUNPOD_API_KEY="invalid" ./components/runpod-client/src/runpod-client validate-auth
```

#### Test 1.2: Pod Operations
```bash
# Test pod creation (will create actual pod - use test image)
POD_ID=$(./components/runpod-client/src/runpod-client create \
    "runpod/base:1.0.0" "NVIDIA GeForce GTX 1080 Ti" 1 0.1 | jq -r '.data.podRentInterruptable.id')

# Test pod retrieval
./components/runpod-client/src/runpod-client get "$POD_ID"

# Clean up test pod
./components/runpod-client/src/runpod-client stop "$POD_ID"
```

### Validation Checkpoints for RunPod Client
- [ ] Authentication properly validates API key
- [ ] GraphQL errors are handled and reported clearly
- [ ] Network failures are handled gracefully
- [ ] JSON responses are validated before processing
- [ ] All required environment variables are checked
- [ ] Pod operations return expected data structures

---

## 2. SSH Manager (`runpod-ssh`)

### Responsibility
Establish, maintain, and execute commands over SSH connections to RunPod instances.

### Implementation Steps

#### Step 2.1: Create SSH Connection Manager
Create `components/runpod-ssh/src/connection.sh`:
```bash
#!/usr/bin/env bash

# Connection configuration
SSH_TIMEOUT=30
SSH_RETRY_ATTEMPTS=5
SSH_RETRY_DELAY=10

establish_connection() {
    local pod_id="$1"
    local host="$2"
    local port="${3:-22}"
    local username="${4:-root}"
    
    # Validation
    [[ -z "$pod_id" ]] && { echo "ERROR: Pod ID required"; exit 1; }
    [[ -z "$host" ]] && { echo "ERROR: Host required"; exit 1; }
    
    local ssh_opts=(
        -o ConnectTimeout=$SSH_TIMEOUT
        -o StrictHostKeyChecking=no
        -o UserKnownHostsFile=/dev/null
        -o LogLevel=ERROR
        -o BatchMode=yes
    )
    
    # Add SSH key if specified
    if [[ -n "${SSH_KEY_PATH:-}" ]]; then
        ssh_opts+=(-i "$SSH_KEY_PATH")
    fi
    
    # Test connection with retry logic
    local attempt=1
    while [[ $attempt -le $SSH_RETRY_ATTEMPTS ]]; do
        if ssh "${ssh_opts[@]}" "$username@$host" -p "$port" "echo 'connection test'" >/dev/null 2>&1; then
            echo "SUCCESS: SSH connection established to $host:$port"
            return 0
        fi
        
        echo "ATTEMPT $attempt/$SSH_RETRY_ATTEMPTS: Connection failed, retrying in ${SSH_RETRY_DELAY}s..."
        sleep $SSH_RETRY_DELAY
        ((attempt++))
        
        # Exponential backoff
        SSH_RETRY_DELAY=$((SSH_RETRY_DELAY * 2))
    done
    
    echo "ERROR: Failed to establish SSH connection after $SSH_RETRY_ATTEMPTS attempts"
    return 1
}

execute_ssh_command() {
    local pod_id="$1"
    local host="$2"
    local command="$3"
    local port="${4:-22}"
    local username="${5:-root}"
    
    local ssh_opts=(
        -o ConnectTimeout=$SSH_TIMEOUT
        -o StrictHostKeyChecking=no
        -o UserKnownHostsFile=/dev/null
        -o LogLevel=ERROR
    )
    
    if [[ -n "${SSH_KEY_PATH:-}" ]]; then
        ssh_opts+=(-i "$SSH_KEY_PATH")
    fi
    
    ssh "${ssh_opts[@]}" "$username@$host" -p "$port" "$command"
}
```

#### Step 2.2: Create Pod Connection Resolver
Create `components/runpod-ssh/src/resolver.sh`:
```bash
#!/usr/bin/env bash

resolve_pod_connection() {
    local pod_id="$1"
    
    # Get pod connection info from runpod-client
    local pod_info
    pod_info=$(runpod-client get "$pod_id") || {
        echo "ERROR: Failed to get pod information"
        exit 1
    }
    
    # Extract connection details
    local host port
    host=$(echo "$pod_info" | jq -r '.data.pod.runtime.ports[] | select(.privatePort == 22) | .ip')
    port=$(echo "$pod_info" | jq -r '.data.pod.runtime.ports[] | select(.privatePort == 22) | .publicPort')
    
    # Validation
    if [[ -z "$host" || "$host" == "null" ]]; then
        echo "ERROR: Could not resolve host for pod $pod_id"
        exit 1
    fi
    
    if [[ -z "$port" || "$port" == "null" ]]; then
        echo "ERROR: Could not resolve SSH port for pod $pod_id"
        exit 1
    fi
    
    echo "$host:$port"
}
```

#### Step 2.3: Create Main SSH Manager
Update `components/runpod-ssh/src/runpod-ssh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/connection.sh"
source "$SCRIPT_DIR/resolver.sh"

show_usage() {
    cat <<EOF
Usage: runpod-ssh <pod_id> <command> [options]

Commands:
    connect         Test SSH connection
    exec <cmd>      Execute command over SSH
    session         Start interactive SSH session
    copy <src> <dst> Copy file to/from pod

Environment Variables:
    SSH_KEY_PATH    Path to SSH private key (optional)
    SSH_USERNAME    SSH username (default: root)
EOF
}

main() {
    local pod_id="$1"
    local command="$2"
    shift 2
    
    # Resolve connection info
    local connection
    connection=$(resolve_pod_connection "$pod_id")
    local host="${connection%:*}"
    local port="${connection#*:}"
    local username="${SSH_USERNAME:-root}"
    
    case "$command" in
        connect)
            establish_connection "$pod_id" "$host" "$port" "$username"
            ;;
        exec)
            local cmd="$1"
            execute_ssh_command "$pod_id" "$host" "$cmd" "$port" "$username"
            ;;
        session)
            ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no \
                -o UserKnownHostsFile=/dev/null "$username@$host" -p "$port"
            ;;
        copy)
            # Implementation for scp/rsync operations
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
```

### Testing Instructions for SSH Manager

#### Test 2.1: Connection Resolution
```bash
# Create test pod first
POD_ID=$(runpod-client create "runpod/base:1.0.0" "NVIDIA GeForce GTX 1080 Ti" 1 0.1 | jq -r '.data.podRentInterruptable.id')

# Wait for pod to be ready (implement wait logic)
sleep 300

# Test connection resolution
./components/runpod-ssh/src/runpod-ssh "$POD_ID" connect
```

#### Test 2.2: Command Execution
```bash
# Test basic command execution
./components/runpod-ssh/src/runpod-ssh "$POD_ID" exec "echo 'Hello from RunPod'"

# Test system information
./components/runpod-ssh/src/runpod-ssh "$POD_ID" exec "nvidia-smi"
```

### Validation Checkpoints for SSH Manager
- [ ] Pod connection info is resolved correctly
- [ ] SSH connections are established within timeout
- [ ] Retry logic works with exponential backoff
- [ ] Commands execute and return output properly
- [ ] Connection failures are handled gracefully
- [ ] SSH key authentication works when configured

---

## 3. Runner Installer (`runner-installer`)

### Responsibility
Manage complete lifecycle of GitHub Actions runners on RunPod instances.

### Implementation Steps

#### Step 3.1: Create Runner Installation Logic
Create `components/runner-installer/src/install.sh`:
```bash
#!/usr/bin/env bash

install_github_runner() {
    local pod_id="$1"
    local repo_url="$2" 
    local runner_token="$3"
    local runner_name="${4:-runpod-runner-$(date +%s)}"
    local work_dir="${WORK_DIR:-/opt/actions-runner}"
    
    # Validation
    [[ -z "$pod_id" ]] && { echo "ERROR: Pod ID required"; exit 1; }
    [[ -z "$repo_url" ]] && { echo "ERROR: Repository URL required"; exit 1; }
    [[ -z "$runner_token" ]] && { echo "ERROR: Runner token required"; exit 1; }
    
    # Installation commands to run on pod
    local install_commands=$(cat <<'EOF'
#!/bin/bash
set -euo pipefail

WORK_DIR="%WORK_DIR%"
REPO_URL="%REPO_URL%"
RUNNER_TOKEN="%RUNNER_TOKEN%"
RUNNER_NAME="%RUNNER_NAME%"

# Create runner directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Download latest runner
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name[1:]')
RUNNER_ARCH="linux-x64"
wget -O actions-runner.tar.gz "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-$RUNNER_ARCH-$RUNNER_VERSION.tar.gz"

# Extract runner
tar xzf actions-runner.tar.gz
rm actions-runner.tar.gz

# Configure runner
./config.sh --url "$REPO_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended

# Install dependencies
sudo ./bin/installdependencies.sh

echo "Runner installed successfully"
EOF
)
    
    # Replace placeholders
    install_commands="${install_commands//%WORK_DIR%/$work_dir}"
    install_commands="${install_commands//%REPO_URL%/$repo_url}"
    install_commands="${install_commands//%RUNNER_TOKEN%/$runner_token}"
    install_commands="${install_commands//%RUNNER_NAME%/$runner_name}"
    
    # Execute installation via SSH
    echo "$install_commands" | runpod-ssh "$pod_id" exec "bash -s"
}

create_runner_service() {
    local pod_id="$1"
    local work_dir="${WORK_DIR:-/opt/actions-runner}"
    
    local service_config=$(cat <<EOF
[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$work_dir
ExecStart=$work_dir/run.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
)
    
    # Create and enable systemd service
    echo "$service_config" | runpod-ssh "$pod_id" exec "cat > /etc/systemd/system/actions-runner.service"
    runpod-ssh "$pod_id" exec "systemctl daemon-reload"
    runpod-ssh "$pod_id" exec "systemctl enable actions-runner"
    runpod-ssh "$pod_id" exec "systemctl start actions-runner"
}
```

#### Step 3.2: Create Runner Management Functions
Create `components/runner-installer/src/manage.sh`:
```bash
#!/usr/bin/env bash

start_runner() {
    local pod_id="$1"
    
    # Try systemd first, fallback to manual
    if runpod-ssh "$pod_id" exec "systemctl start actions-runner" 2>/dev/null; then
        echo "Runner started via systemd"
    else
        echo "Systemd failed, starting manually"
        runpod-ssh "$pod_id" exec "cd ${WORK_DIR:-/opt/actions-runner} && nohup ./run.sh > runner.log 2>&1 &"
    fi
}

stop_runner() {
    local pod_id="$1"
    
    # Try systemd first
    if runpod-ssh "$pod_id" exec "systemctl stop actions-runner" 2>/dev/null; then
        echo "Runner stopped via systemd"
    else
        # Find and kill runner processes
        runpod-ssh "$pod_id" exec "pkill -f 'Runner.Worker' || true"
        echo "Runner processes terminated"
    fi
}

get_runner_status() {
    local pod_id="$1"
    
    # Check systemd status
    if runpod-ssh "$pod_id" exec "systemctl is-active actions-runner" >/dev/null 2>&1; then
        echo "RUNNING (systemd)"
        return 0
    fi
    
    # Check for running processes
    if runpod-ssh "$pod_id" exec "pgrep -f 'Runner.Worker'" >/dev/null 2>&1; then
        echo "RUNNING (manual)"
        return 0
    fi
    
    echo "STOPPED"
    return 1
}

remove_runner() {
    local pod_id="$1"
    local repo_url="$2"
    local remove_token="$3"
    local work_dir="${WORK_DIR:-/opt/actions-runner}"
    
    # Stop runner first
    stop_runner "$pod_id"
    
    # Remove from GitHub
    if [[ -n "$remove_token" ]]; then
        runpod-ssh "$pod_id" exec "cd $work_dir && ./config.sh remove --token $remove_token"
    fi
    
    # Clean up files
    runpod-ssh "$pod_id" exec "rm -rf $work_dir"
    runpod-ssh "$pod_id" exec "systemctl disable actions-runner 2>/dev/null || true"
    runpod-ssh "$pod_id" exec "rm -f /etc/systemd/system/actions-runner.service"
}
```

### Testing Instructions for Runner Installer

#### Test 3.1: Runner Installation
```bash
# Generate runner token (requires GitHub CLI or API)
RUNNER_TOKEN=$(gh api repos/$REPO/actions/runners/registration-token --jq .token)

# Test installation
./components/runner-installer/src/runner-installer install "$POD_ID" \
    "https://github.com/user/repo" "$RUNNER_TOKEN" "test-runner"
```

#### Test 3.2: Service Management  
```bash
# Test runner status
./components/runner-installer/src/runner-installer status "$POD_ID"

# Test stop/start
./components/runner-installer/src/runner-installer stop "$POD_ID"
./components/runner-installer/src/runner-installer start "$POD_ID"
```

### Validation Checkpoints for Runner Installer
- [ ] Runner downloads and extracts properly
- [ ] Configuration completes without errors
- [ ] Systemd service is created and starts
- [ ] Manual fallback works when systemd unavailable
- [ ] Runner appears in GitHub repository settings
- [ ] Runner can execute simple jobs

---

## 4. Pod Lifecycle Manager (`pod-lifecycle-manager`)

### Responsibility
Coordinate pod state transitions and maintain comprehensive pod inventory.

### Implementation Steps

#### Step 4.1: Create State Tracking
Create `components/pod-lifecycle-manager/src/state.sh`:
```bash
#!/usr/bin/env bash

PODS_STATE_FILE="${PODS_STATE_FILE:-$HOME/.runpod-pods.json}"

init_state_file() {
    if [[ ! -f "$PODS_STATE_FILE" ]]; then
        echo '{"pods": []}' > "$PODS_STATE_FILE"
    fi
}

add_pod_to_state() {
    local pod_id="$1"
    local status="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    init_state_file
    
    local new_pod=$(cat <<EOF
{
    "id": "$pod_id",
    "status": "$status", 
    "created": "$timestamp",
    "last_updated": "$timestamp"
}
EOF
)
    
    # Add pod to state file
    local temp_file=$(mktemp)
    jq --argjson pod "$new_pod" '.pods += [$pod]' "$PODS_STATE_FILE" > "$temp_file"
    mv "$temp_file" "$PODS_STATE_FILE"
}

update_pod_state() {
    local pod_id="$1"
    local status="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    init_state_file
    
    local temp_file=$(mktemp)
    jq --arg pod_id "$pod_id" --arg status "$status" --arg timestamp "$timestamp" '
        .pods |= map(if .id == $pod_id then .status = $status | .last_updated = $timestamp else . end)
    ' "$PODS_STATE_FILE" > "$temp_file"
    mv "$temp_file" "$PODS_STATE_FILE"
}

get_pod_state() {
    local pod_id="$1"
    
    init_state_file
    jq -r --arg pod_id "$pod_id" '.pods[] | select(.id == $pod_id) | .status' "$PODS_STATE_FILE"
}

list_pods() {
    local status_filter="${1:-}"
    
    init_state_file
    if [[ -n "$status_filter" ]]; then
        jq -r --arg status "$status_filter" '.pods[] | select(.status == $status) | "\(.id) \(.status) \(.last_updated)"' "$PODS_STATE_FILE"
    else
        jq -r '.pods[] | "\(.id) \(.status) \(.last_updated)"' "$PODS_STATE_FILE"
    fi
}
```

#### Step 4.2: Create Pod Management Operations
Create `components/pod-lifecycle-manager/src/operations.sh`:
```bash
#!/usr/bin/env bash

source "$(dirname "$0")/state.sh"

create_managed_pod() {
    local image="$1"
    local gpu_type="$2" 
    local gpu_count="${3:-1}"
    local bid_price="${4:-0.5}"
    
    echo "Creating pod with image: $image, GPU: $gpu_type, Count: $gpu_count, Bid: $bid_price"
    
    # Create pod via runpod-client
    local result
    result=$(runpod-client create "$image" "$gpu_type" "$gpu_count" "$bid_price")
    
    local pod_id
    pod_id=$(echo "$result" | jq -r '.data.podRentInterruptable.id')
    
    if [[ "$pod_id" == "null" || -z "$pod_id" ]]; then
        echo "ERROR: Failed to create pod"
        echo "$result" >&2
        exit 1
    fi
    
    # Add to state tracking
    add_pod_to_state "$pod_id" "PENDING"
    
    echo "Pod created successfully: $pod_id"
    echo "$pod_id"
}

wait_for_pod_ready() {
    local pod_id="$1"
    local timeout="${2:-600}"  # 10 minutes default
    local check_interval=30
    local elapsed=0
    
    echo "Waiting for pod $pod_id to be ready (timeout: ${timeout}s)"
    
    while [[ $elapsed -lt $timeout ]]; do
        local pod_info
        pod_info=$(runpod-client get "$pod_id")
        
        local status
        status=$(echo "$pod_info" | jq -r '.data.pod.desiredStatus')
        
        local runtime_ports
        runtime_ports=$(echo "$pod_info" | jq -r '.data.pod.runtime.ports // empty')
        
        if [[ "$status" == "RUNNING" && -n "$runtime_ports" ]]; then
            update_pod_state "$pod_id" "RUNNING"
            echo "Pod $pod_id is ready"
            return 0
        fi
        
        echo "Pod status: $status, waiting..."
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo "ERROR: Pod $pod_id not ready after ${timeout}s"
    update_pod_state "$pod_id" "TIMEOUT"
    return 1
}

stop_managed_pod() {
    local pod_id="$1"
    
    echo "Stopping pod: $pod_id"
    
    local result
    result=$(runpod-client stop "$pod_id")
    
    # Update state
    update_pod_state "$pod_id" "STOPPING"
    
    echo "Stop request sent for pod: $pod_id"
}

get_comprehensive_status() {
    local pod_id="$1"
    
    # Get API status
    local api_status
    api_status=$(runpod-client get "$pod_id")
    
    # Get local state
    local local_status
    local_status=$(get_pod_state "$pod_id")
    
    # Combine information
    echo "=== Pod Status: $pod_id ==="
    echo "Local state: $local_status"
    echo "API Status:"
    echo "$api_status" | jq '.'
}
```

### Testing Instructions for Pod Lifecycle Manager

#### Test 4.1: State Management
```bash
# Test state initialization
rm -f ~/.runpod-pods.json
./components/pod-lifecycle-manager/src/pod-lifecycle-manager list

# Create and track pod
POD_ID=$(./components/pod-lifecycle-manager/src/pod-lifecycle-manager create \
    "runpod/base:1.0.0" "NVIDIA GeForce GTX 1080 Ti" 1 0.1)

# Check state was recorded
./components/pod-lifecycle-manager/src/pod-lifecycle-manager list
```

#### Test 4.2: Pod Readiness
```bash
# Test wait functionality
./components/pod-lifecycle-manager/src/pod-lifecycle-manager wait "$POD_ID" 300

# Test status reporting
./components/pod-lifecycle-manager/src/pod-lifecycle-manager status "$POD_ID"
```

### Validation Checkpoints for Pod Lifecycle Manager
- [ ] State file is created and maintained properly
- [ ] Pod creation is tracked with timestamps
- [ ] Pod status updates are recorded correctly
- [ ] Wait logic correctly detects pod readiness
- [ ] List operations filter by status
- [ ] State persistence survives script restarts

---

## 5. Workflow Orchestrator (`workflow-orchestrator`)

### Responsibility
Coordinate end-to-end workflows integrating all components with comprehensive error recovery.

### Implementation Steps

#### Step 5.1: Create Workflow Definitions
Create `components/workflow-orchestrator/src/workflows.sh`:
```bash
#!/usr/bin/env bash

workflow_setup_runner() {
    local config_file="$1"
    
    # Load configuration
    local image gpu_type gpu_count bid_price repo_url runner_token runner_name
    eval "$(jq -r 'to_entries[] | "\(.key)=\(.value|tostring)"' "$config_file")"
    
    echo "=== Starting Runner Setup Workflow ==="
    echo "Image: $image"
    echo "GPU: $gpu_type ($gpu_count units)"
    echo "Repository: $repo_url"
    echo "Runner: $runner_name"
    
    # Step 1: Create pod
    echo "Step 1/5: Creating pod..."
    local pod_id
    pod_id=$(pod-lifecycle-manager create "$image" "$gpu_type" "$gpu_count" "$bid_price")
    
    # Step 2: Wait for readiness
    echo "Step 2/5: Waiting for pod readiness..."
    if ! pod-lifecycle-manager wait "$pod_id" 600; then
        echo "ERROR: Pod not ready, aborting workflow"
        cleanup_failed_workflow "$pod_id"
        exit 1
    fi
    
    # Step 3: Test SSH connection
    echo "Step 3/5: Testing SSH connection..."
    if ! runpod-ssh "$pod_id" connect; then
        echo "ERROR: SSH connection failed, aborting workflow"
        cleanup_failed_workflow "$pod_id"
        exit 1
    fi
    
    # Step 4: Install runner
    echo "Step 4/5: Installing GitHub Actions runner..."
    if ! runner-installer install "$pod_id" "$repo_url" "$runner_token" "$runner_name"; then
        echo "ERROR: Runner installation failed, aborting workflow"
        cleanup_failed_workflow "$pod_id"
        exit 1
    fi
    
    # Step 5: Validate runner
    echo "Step 5/5: Validating runner status..."
    if ! runner-installer status "$pod_id" | grep -q "RUNNING"; then
        echo "ERROR: Runner not running, aborting workflow"
        cleanup_failed_workflow "$pod_id"
        exit 1
    fi
    
    echo "=== Workflow Completed Successfully ==="
    echo "Pod ID: $pod_id"
    echo "Runner: $runner_name"
    echo "Status: Active and ready for jobs"
}

workflow_teardown_runner() {
    local pod_id="$1"
    local repo_url="$2"
    local remove_token="${3:-}"
    
    echo "=== Starting Runner Teardown Workflow ==="
    
    # Step 1: Stop runner
    echo "Step 1/3: Stopping runner..."
    runner-installer stop "$pod_id" || echo "Warning: Runner stop failed"
    
    # Step 2: Remove runner (if token provided)
    if [[ -n "$remove_token" ]]; then
        echo "Step 2/3: Removing runner from GitHub..."
        runner-installer remove "$pod_id" "$repo_url" "$remove_token" || echo "Warning: Runner removal failed"
    else
        echo "Step 2/3: Skipping runner removal (no token)"
    fi
    
    # Step 3: Stop pod
    echo "Step 3/3: Stopping pod..."
    pod-lifecycle-manager stop "$pod_id"
    
    echo "=== Teardown Workflow Completed ==="
}

cleanup_failed_workflow() {
    local pod_id="$1"
    
    echo "=== Cleaning up failed workflow ==="
    echo "Pod ID: $pod_id"
    
    # Best effort cleanup
    runner-installer stop "$pod_id" 2>/dev/null || true
    pod-lifecycle-manager stop "$pod_id" 2>/dev/null || true
    
    echo "=== Cleanup completed ==="
}
```

#### Step 5.2: Create Multi-Pod Support
Create `components/workflow-orchestrator/src/multi-pod.sh`:
```bash
#!/usr/bin/env bash

workflow_multi_pod_setup() {
    local config_file="$1"
    local max_parallel="${2:-3}"
    
    # Parse configuration for multiple pod definitions
    local pod_count
    pod_count=$(jq -r '.pods | length' "$config_file")
    
    echo "=== Starting Multi-Pod Setup Workflow ==="
    echo "Pod count: $pod_count"
    echo "Max parallel: $max_parallel"
    
    local active_jobs=0
    local completed_pods=0
    local failed_pods=0
    
    for i in $(seq 0 $((pod_count - 1))); do
        # Extract pod configuration
        local pod_config
        pod_config=$(jq -r ".pods[$i]" "$config_file")
        
        # Start pod setup in background if under parallel limit
        if [[ $active_jobs -lt $max_parallel ]]; then
            setup_single_pod_async "$pod_config" &
            ((active_jobs++))
        else
            # Wait for a job to complete
            wait -n
            ((active_jobs--))
            setup_single_pod_async "$pod_config" &
            ((active_jobs++))
        fi
    done
    
    # Wait for all jobs to complete
    wait
    
    echo "=== Multi-Pod Setup Completed ==="
    echo "Total pods: $pod_count"
    echo "Success: $((pod_count - failed_pods))"
    echo "Failed: $failed_pods"
}

setup_single_pod_async() {
    local pod_config="$1"
    local temp_config=$(mktemp)
    
    echo "$pod_config" > "$temp_config"
    
    if workflow_setup_runner "$temp_config"; then
        echo "SUCCESS: Pod setup completed"
    else
        echo "FAILED: Pod setup failed"
        exit 1
    fi
    
    rm -f "$temp_config"
}
```

### Testing Instructions for Workflow Orchestrator

#### Test 5.1: Single Runner Workflow
Create test configuration file `test-config.json`:
```json
{
    "image": "runpod/base:1.0.0",
    "gpu_type": "NVIDIA GeForce GTX 1080 Ti",
    "gpu_count": 1,
    "bid_price": 0.1,
    "repo_url": "https://github.com/user/test-repo",
    "runner_token": "GHRT_...",
    "runner_name": "test-runner"
}
```

Test workflow:
```bash
# Test complete setup workflow
./components/workflow-orchestrator/src/workflow-orchestrator setup-runner test-config.json

# Test teardown
./components/workflow-orchestrator/src/workflow-orchestrator teardown-runner "$POD_ID" "https://github.com/user/test-repo"
```

### Validation Checkpoints for Workflow Orchestrator
- [ ] All workflow steps execute in correct order
- [ ] Failures at any step trigger proper cleanup
- [ ] Multiple pods can be managed simultaneously
- [ ] Progress reporting is clear and informative
- [ ] Configuration loading works correctly
- [ ] Error recovery mechanisms function properly

---

## 6. Configuration Manager (`configuration-manager`)

### Implementation Steps

#### Step 6.1: Create Environment Validation
Create `components/configuration-manager/src/validation.sh`:
```bash
#!/usr/bin/env bash

validate_environment() {
    local errors=0
    
    echo "=== Environment Validation ==="
    
    # Required environment variables
    local required_vars=(
        "RUNPOD_API_KEY"
        "GITHUB_TOKEN"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            echo "ERROR: $var is not set"
            ((errors++))
        else
            echo "✓ $var is set"
        fi
    done
    
    # Optional environment variables with defaults
    local optional_vars=(
        "RUNPOD_API_URL:https://api.runpod.io/graphql"
        "SSH_USERNAME:root"
        "WORK_DIR:/opt/actions-runner"
    )
    
    for var_default in "${optional_vars[@]}"; do
        local var="${var_default%:*}"
        local default="${var_default#*:}"
        
        if [[ -z "${!var:-}" ]]; then
            export "$var"="$default"
            echo "ℹ $var set to default: $default"
        else
            echo "✓ $var is set: ${!var}"
        fi
    done
    
    # Tool availability
    local required_tools=(
        "curl"
        "jq"
        "ssh"
        "gh"
    )
    
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo "✓ $tool is available"
        else
            echo "ERROR: $tool is not available"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        echo "✓ Environment validation passed"
        return 0
    else
        echo "✗ Environment validation failed with $errors errors"
        return 1
    fi
}
```

### Testing Instructions for Configuration Manager

#### Test 6.1: Environment Validation
```bash
# Test with missing variables
unset RUNPOD_API_KEY
./components/configuration-manager/src/configuration-manager validate-env

# Test with all variables set
export RUNPOD_API_KEY="test_key"
export GITHUB_TOKEN="test_token"
./components/configuration-manager/src/configuration-manager validate-env
```

---

## Integration Testing

### Full System Integration Test

Create `tests/integration-test.sh`:
```bash
#!/usr/bin/env bash

run_integration_test() {
    echo "=== RunPod SSH Flake Integration Test ==="
    
    # Step 1: Environment validation
    echo "Step 1: Validating environment..."
    if ! configuration-manager validate-env; then
        echo "FAILED: Environment validation"
        exit 1
    fi
    
    # Step 2: API connectivity
    echo "Step 2: Testing API connectivity..."
    if ! runpod-client validate-auth; then
        echo "FAILED: API authentication"
        exit 1
    fi
    
    # Step 3: Create test pod (small/cheap instance)
    echo "Step 3: Creating test pod..."
    local pod_id
    pod_id=$(pod-lifecycle-manager create "runpod/base:1.0.0" "NVIDIA GeForce GTX 1080 Ti" 1 0.05)
    
    if [[ -z "$pod_id" ]]; then
        echo "FAILED: Pod creation"
        exit 1
    fi
    
    # Step 4: Wait for pod readiness
    echo "Step 4: Waiting for pod readiness..."
    if ! pod-lifecycle-manager wait "$pod_id" 300; then
        echo "FAILED: Pod not ready"
        cleanup_test_pod "$pod_id"
        exit 1
    fi
    
    # Step 5: Test SSH connectivity
    echo "Step 5: Testing SSH connection..."
    if ! runpod-ssh "$pod_id" exec "echo 'SSH test successful'"; then
        echo "FAILED: SSH connection"
        cleanup_test_pod "$pod_id"
        exit 1
    fi
    
    # Step 6: Cleanup
    echo "Step 6: Cleaning up test pod..."
    cleanup_test_pod "$pod_id"
    
    echo "✓ Integration test passed"
}

cleanup_test_pod() {
    local pod_id="$1"
    pod-lifecycle-manager stop "$pod_id" || true
}

run_integration_test
```

## Final Validation Checklist

### Component Completion Checklist
- [ ] RunPod Client: All operations implemented and tested
- [ ] SSH Manager: Connection management and command execution working
- [ ] Runner Installer: Complete lifecycle management implemented  
- [ ] Pod Lifecycle Manager: State tracking and operations complete
- [ ] Workflow Orchestrator: End-to-end workflows functional
- [ ] Configuration Manager: Environment validation and defaults working

### Integration Validation  
- [ ] All components can communicate through defined interfaces
- [ ] Error handling propagates correctly between components
- [ ] Configuration is consistently applied across components
- [ ] Cleanup operations work reliably
- [ ] Multi-pod scenarios function properly
- [ ] Performance meets specified targets

### Documentation Validation
- [ ] All implementation steps are clearly documented
- [ ] Testing instructions are complete and accurate
- [ ] Error scenarios and recovery procedures are documented
- [ ] Configuration options are fully explained
- [ ] Integration points are well-defined

## Worker Handoff Protocol

When implementation is complete, provide:

1. **Component Status Report**
   - Implementation completion status for each component
   - Test results for all validation checkpoints
   - Any deviations from specifications

2. **Integration Test Results**
   - Full system integration test results
   - Performance benchmarks
   - Error handling verification

3. **Configuration Documentation**
   - All environment variables and their purposes
   - Configuration file formats and examples
   - Default values and override mechanisms

4. **Operational Procedures**
   - Deployment instructions
   - Monitoring and troubleshooting guides
   - Maintenance procedures

This completes the comprehensive implementation instructions for the RunPod SSH Flake system. Each Worker should follow these instructions precisely and provide detailed validation results upon completion.