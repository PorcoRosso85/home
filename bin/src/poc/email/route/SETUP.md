# Email Archive POC Setup Guide

This guide provides step-by-step instructions for setting up the Email Archive POC with MinIO storage.

## Quick Start

1. **Initialize MinIO and bucket:**
   ```bash
   # Run the automated setup script
   ./setup-minio.sh --keep-running
   ```

2. **Verify setup:**
   ```bash
   # Run health checks
   ./health-check.sh --performance
   ```

3. **Start development:**
   ```bash
   # Start Worker development server
   nix run .#dev-worker
   ```

## Detailed Setup Instructions

### Prerequisites

- Nix package manager installed
- This project uses Nix flakes for dependency management

### Step 1: Environment Setup

1. **Copy environment configuration:**
   ```bash
   cp .env.example .env.development
   ```

2. **Customize settings** (optional):
   Edit `.env.development` to match your preferences:
   ```bash
   # Example customizations
   MINIO_ACCESS_KEY=your_custom_key
   MINIO_SECRET_KEY=your_custom_secret
   BUCKET_NAME=my-email-archive
   ```

### Step 2: MinIO Server Setup

#### Option A: Automated Setup (Recommended)

Use the provided setup script:

```bash
# Set up and start MinIO with bucket creation
./setup-minio.sh --keep-running

# In another terminal, verify the setup
./health-check.sh
```

#### Option B: Manual Setup

1. **Start MinIO server:**
   ```bash
   nix run .#start-minio
   ```

2. **Create and configure bucket:**
   ```bash
   # In another terminal
   nix run .#setup-bucket
   ```

3. **Verify setup:**
   ```bash
   ./health-check.sh --performance
   ```

### Step 3: Development Environment

1. **Enter development shell:**
   ```bash
   nix develop
   ```

2. **Start Worker development server:**
   ```bash
   nix run .#dev-worker
   ```

3. **Test email archiving:**
   ```bash
   nix run .#test-archive
   ```

## Configuration Files

### Environment Files

- **`.env.development`** - Development-specific configuration
- **`.env.example`** - Template for environment variables
- **`docker.env`** - Docker/containerized deployment settings

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | `http://localhost:9000` | MinIO API endpoint |
| `MINIO_CONSOLE_URL` | `http://localhost:9001` | MinIO web console |
| `BUCKET_NAME` | `email-archive` | S3 bucket for email storage |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access credentials |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret credentials |

## Scripts Overview

### Setup Script (`setup-minio.sh`)

Automated MinIO initialization with comprehensive setup:

- ✅ Dependency checking
- ✅ MinIO server startup
- ✅ Bucket creation and configuration
- ✅ Access policy setup
- ✅ Test data structure creation
- ✅ Status reporting

**Usage:**
```bash
./setup-minio.sh [--keep-running] [--help]
```

### Health Check Script (`health-check.sh`)

Comprehensive system verification:

- ✅ MinIO server responsiveness
- ✅ Bucket accessibility and permissions
- ✅ System resource monitoring
- ✅ Performance testing
- ✅ Dependency verification

**Usage:**
```bash
./health-check.sh [--performance] [--help]
```

## Verification Steps

### 1. Basic Health Check

```bash
./health-check.sh
```

Expected output:
```
[PASS] MinIO server is running and responding
[PASS] MinIO server is ready to accept requests
[PASS] MinIO console is accessible
[PASS] MinIO client can authenticate with server
[PASS] Bucket 'email-archive' is accessible
[PASS] Bucket has write permissions
[PASS] All required dependencies are available
[PASS] Disk space is sufficient (15% used)

Checks passed: 8/8
[SUCCESS] All health checks passed! System is ready for email archiving.
```

### 2. Performance Testing

```bash
./health-check.sh --performance
```

This includes upload/download timing tests.

### 3. Manual Verification

1. **Access MinIO Console:**
   - URL: http://localhost:9001
   - Login: minioadmin / minioadmin
   - Verify `email-archive` bucket exists

2. **Test API Access:**
   ```bash
   curl http://localhost:9000/minio/health/live
   # Should return: OK
   ```

3. **List Bucket Contents:**
   ```bash
   mc alias set local http://localhost:9000 minioadmin minioadmin
   mc ls local/email-archive --recursive
   ```

## Troubleshooting

### Common Issues

1. **MinIO won't start:**
   ```bash
   # Check if port is in use
   lsof -i :9000
   
   # Kill existing MinIO process
   pkill minio
   ```

2. **Bucket creation fails:**
   ```bash
   # Verify MinIO is running
   curl http://localhost:9000/minio/health/live
   
   # Manually create bucket
   mc mb local/email-archive
   ```

3. **Permission errors:**
   ```bash
   # Reset bucket policy
   mc anonymous set download local/email-archive
   mc anonymous set upload local/email-archive
   ```

4. **Health check failures:**
   ```bash
   # Check logs
   tail -f ./minio-data/.minio.sys/logs/api.log
   
   # Verify connectivity
   curl -v http://localhost:9000/minio/health/ready
   ```

### Log Files

- MinIO logs: `./minio-data/.minio.sys/logs/`
- Setup script creates: `.minio.pid` (process ID)
- Health check creates temporary test files

### Recovery Steps

1. **Clean restart:**
   ```bash
   # Stop MinIO
   kill $(cat .minio.pid) 2>/dev/null || true
   rm .minio.pid
   
   # Clean data (optional - removes all stored emails)
   rm -rf ./minio-data
   
   # Run setup again
   ./setup-minio.sh --keep-running
   ```

2. **Reset configuration:**
   ```bash
   mc alias remove local
   ./setup-minio.sh --keep-running
   ```

## Next Steps

After successful setup:

1. **Configure Cloudflare Worker:**
   - Deploy the Worker code to Cloudflare
   - Set environment variables for your MinIO endpoint
   - Configure Email Routing rules

2. **Set up monitoring:**
   - Use the health check script in cron jobs
   - Monitor MinIO metrics via the console
   - Set up log rotation for long-term operation

3. **Production deployment:**
   - Review security settings
   - Configure proper access keys
   - Set up SSL/TLS for MinIO
   - Configure backup and retention policies

## Security Notes

- Default credentials (`minioadmin/minioadmin`) are for development only
- Change access keys for production deployment
- Consider enabling MinIO's encryption features
- Implement proper firewall rules for production
- Review bucket policies for least-privilege access

## Support

For issues specific to this POC:
1. Run `./health-check.sh` for diagnostic information
2. Check MinIO logs in `./minio-data/.minio.sys/logs/`
3. Verify all dependencies are installed via `nix develop`

For MinIO-specific issues, refer to the [MinIO documentation](https://docs.min.io/).