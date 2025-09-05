# RunPod SSH Flake - GitHub Actions Runner Integration

A Nix flake that provides seamless integration between RunPod GPU instances and GitHub Actions self-hosted runners over SSH connections.

## Overview

This flake enables you to:
- Create and manage RunPod GPU instances via GraphQL API
- Establish secure SSH connections to RunPod pods
- Install and manage GitHub Actions runners on RunPod instances
- Automate the entire workflow through GitHub Actions

## Architecture

```
GitHub Actions Workflow
       ↓
  RunPod GraphQL API
       ↓
   Pod Management
       ↓
  SSH Connection
       ↓
GitHub Actions Runner
```

## Features

- **Pod Lifecycle Management**: Create, start, stop, and monitor RunPod instances
- **SSH Connection Management**: Secure SSH connections with retry logic and error handling
- **GitHub Actions Integration**: Automated runner installation and configuration
- **Workflow Automation**: Complete GitHub Actions workflow for pod management
- **Multi-Pod Support**: Job matrix for multiple concurrent runners
- **Monitoring and Cleanup**: Automated monitoring and cleanup of long-running pods

## Prerequisites

- RunPod API key
- GitHub repository with Actions enabled
- Nix with flakes support
- SSH key pair (optional, for key-based authentication)

## Quick Start

### 1. Setup API Key

Get your RunPod API key from [RunPod Console](https://www.runpod.io/console) and set it as an environment variable:

```bash
export RUNPOD_API_KEY="your_runpod_api_key_here"
```

### 2. Build the Tools

```bash
nix build .#default
```

Or enter the development shell:

```bash
nix develop
```

### 3. Create and Setup a Pod

```bash
# Create a new pod
POD_ID=$(./scripts/pod-lifecycle.sh create)
echo "Created pod: $POD_ID"

# Setup GitHub Actions runner
./scripts/ssh-runner.sh setup $POD_ID https://github.com/your/repo $RUNNER_TOKEN
```

### 4. Use GitHub Actions Workflow

Add the provided workflow to your repository at `.github/workflows/runpod-runner.yml` and configure the required secrets.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RUNPOD_API_KEY` | RunPod API authentication key | Yes |
| `RUNPOD_API_URL` | API endpoint (default: https://api.runpod.io/graphql) | No |

### GitHub Secrets

Configure these secrets in your GitHub repository:

| Secret | Description |
|--------|-------------|
| `RUNPOD_API_KEY` | Your RunPod API key |
| `GITHUB_TOKEN` | GitHub token for runner registration (automatically provided) |

## Commands

### Pod Lifecycle Management

```bash
# Create a new pod
./scripts/pod-lifecycle.sh create [image] [gpu_type] [gpu_count] [bid_price]

# Resume a stopped pod
./scripts/pod-lifecycle.sh resume <pod_id>

# Stop a running pod
./scripts/pod-lifecycle.sh stop <pod_id>

# Check pod status
./scripts/pod-lifecycle.sh status <pod_id>

# List all pods
./scripts/pod-lifecycle.sh list

# Wait for pod to be ready
./scripts/pod-lifecycle.sh wait <pod_id> [timeout_seconds]

# Display connection information
./scripts/pod-lifecycle.sh info <pod_id>
```

### SSH and Runner Management

```bash
# Setup complete pod with GitHub Actions runner
./scripts/ssh-runner.sh setup <pod_id> <repo_url> <runner_token> [runner_name]

# Install runner only
./scripts/ssh-runner.sh install <pod_id> <repo_url> <runner_token> [runner_name]

# Check runner status
./scripts/ssh-runner.sh status <pod_id>

# Stop runner
./scripts/ssh-runner.sh stop <pod_id>

# Remove runner completely
./scripts/ssh-runner.sh remove <pod_id> [remove_token]

# Interactive SSH session
./scripts/ssh-runner.sh ssh <pod_id>

# Monitor runner logs
./scripts/ssh-runner.sh logs <pod_id>

# Execute command over SSH
./scripts/ssh-runner.sh exec <pod_id> '<command>'
```

## Usage Examples

### Basic Pod Creation and Runner Setup

```bash
# Set API key
export RUNPOD_API_KEY="your_api_key"

# Create pod with specific GPU type
POD_ID=$(./scripts/pod-lifecycle.sh create \
  "runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04" \
  "NVIDIA GeForce RTX 4090" \
  1 \
  0.5)

# Generate GitHub runner token (using GitHub CLI)
RUNNER_TOKEN=$(gh api \
  repos/:owner/:repo/actions/runners/registration-token \
  --jq .token)

# Setup runner
./scripts/ssh-runner.sh setup $POD_ID \
  "https://github.com/your/repo" \
  "$RUNNER_TOKEN" \
  "my-runpod-runner"
```

### GitHub Actions Workflow Usage

1. **Manual Trigger**: Use workflow dispatch to create/manage pods
2. **Automated Setup**: The workflow can create pods and setup runners automatically
3. **Multi-Pod Matrix**: Run jobs across multiple pod configurations
4. **Scheduled Cleanup**: Automatic cleanup of old pods

### Programmatic Usage with Nix

```bash
# Use the runpod-client directly
nix run .#runpod-client -- status <pod_id>

# Use SSH manager
nix run .#runpod-ssh -- <pod_id> "nvidia-smi"

# Use runner installer
nix run .#runner-installer -- <repo_url> <token> <name>
```

## Advanced Configuration

### Custom Docker Images

Specify custom Docker images when creating pods:

```bash
./scripts/pod-lifecycle.sh create \
  "your-registry/custom-image:tag" \
  "NVIDIA A100 80GB PCIe" \
  2 \
  1.0
```

### SSH Key Authentication

Use custom SSH keys:

```bash
# Generate key pair
ssh-keygen -t ed25519 -f ~/.ssh/runpod_key

# Use custom key
SSH_KEY_PATH=~/.ssh/runpod_key ./scripts/ssh-runner.sh ssh <pod_id>
```

### Multiple Runners per Pod

Run multiple runners on a single pod:

```bash
# Install first runner
./scripts/ssh-runner.sh install $POD_ID $REPO_URL $TOKEN1 "runner-1"

# Install second runner in different directory
WORK_DIR="/opt/actions-runner-2" ./scripts/ssh-runner.sh install \
  $POD_ID $REPO_URL $TOKEN2 "runner-2"
```

## Monitoring and Troubleshooting

### Check Pod Status

```bash
# Detailed status
./scripts/pod-lifecycle.sh status <pod_id>

# Connection info
./scripts/pod-lifecycle.sh info <pod_id>
```

### Monitor Runner Logs

```bash
# Live log monitoring
./scripts/ssh-runner.sh logs <pod_id>

# Execute diagnostics
./scripts/ssh-runner.sh exec <pod_id> "systemctl status actions.runner.*"
```

### Common Issues

1. **Pod Not Ready**: Wait longer or check RunPod dashboard
2. **SSH Connection Failed**: Verify pod has SSH enabled and is running
3. **Runner Not Starting**: Check runner logs and system dependencies
4. **API Rate Limits**: Implement exponential backoff (built into scripts)

## Security Considerations

- API keys are sensitive - use GitHub secrets
- SSH connections use secure defaults (StrictHostKeyChecking=no for ephemeral pods)
- Runner tokens are short-lived and automatically masked
- Consider using SSH key authentication for enhanced security

## Performance Optimization

- Use appropriate GPU types for workloads
- Set competitive bid prices for better availability
- Monitor and cleanup unused pods to reduce costs
- Use spot instances (interruptible) for cost savings

## Development

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

### Testing

```bash
# Test pod lifecycle
./scripts/pod-lifecycle.sh create test-image
./scripts/pod-lifecycle.sh status <test_pod_id>
./scripts/pod-lifecycle.sh stop <test_pod_id>

# Test SSH connectivity
./scripts/ssh-runner.sh exec <pod_id> "echo 'Connection test successful'"
```

## License

MIT License - see LICENSE file for details.

## Support

- RunPod API Documentation: https://docs.runpod.io/
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Issues: Create an issue in this repository