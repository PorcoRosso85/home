# nixd LSP Verification Guide

## Overview
This document provides comprehensive verification procedures for nixd LSP integration within the LSIF indexer project. Use this guide to verify that nixd is properly configured, accessible, and functional in your development environment.

## Environment Setup Checklist

### 1. Nix Development Environment
- [ ] `nix develop` command works in project directory
- [ ] Development shell activates successfully
- [ ] All dependencies are available

### 2. Required Environment Variables
The following environment variables should be automatically set in the nix develop shell:

```bash
# Automatically set by flake.nix
NIXD_PATH=/nix/store/.../bin/nixd          # Path to nixd binary
RUST_ANALYZER_PATH=/nix/store/.../bin/rust-analyzer  # Path to rust-analyzer
```

### 3. Manual Environment Variable Setup (if needed)
If environment variables are not set automatically:

```bash
export NIXD_PATH=$(which nixd)
export RUST_ANALYZER_PATH=$(which rust-analyzer)
export LSIF_ENABLED_LANGUAGES=nix  # For nix-only testing
```

## Step-by-Step Verification Commands

### Step 1: Basic nixd Availability
```bash
# Check if nixd is available
which nixd
# Expected output: /nix/store/.../bin/nixd

# Check nixd version
nixd --version
# Expected output: nixd version information

# Verify nixd binary is executable
ls -la $(which nixd)
# Expected output: Executable permissions (-rwxr-xr-x)
```

### Step 2: Nix Development Shell Verification
```bash
# Enter nix development shell
nix develop

# Verify environment variables are set
echo "NIXD_PATH: $NIXD_PATH"
echo "RUST_ANALYZER_PATH: $RUST_ANALYZER_PATH"

# Expected output:
# NIXD_PATH: /nix/store/.../bin/nixd
# RUST_ANALYZER_PATH: /nix/store/.../bin/rust-analyzer
```

### Step 3: Project Build Verification
```bash
# Build the project (within nix develop)
cargo build
# Expected: Successful build without errors

# Build release version
cargo build --release
# Expected: Release binary created in target/release/
```

### Step 4: LSP Client Test
```bash
# Test nixd LSP startup (nix-only mode)
LSIF_ENABLED_LANGUAGES=nix RUST_LOG=debug cargo run -p cli --bin lsif -- index --force

# Look for these log messages:
# - "Warming up LSP clients for ENABLED languages only: ["nix"]"
# - "🔧 Initializing LSP server for nix"
# - "✅ Successfully warmed up LSP client for nix"
# - "nixd LSP startup validated"
```

### Step 5: Comprehensive Integration Test
```bash
# Run the automated verification script
./scripts/verify-nixd.sh

# Expected: All tests pass with success indicators
```

## Expected Outputs

### Successful nixd LSP Integration
When nixd LSP is working correctly, you should see:

```
🚀 Starting LSP warm-up for 1 language(s): {"nix"}
🔧 Initializing LSP server for nix
✅ Successfully warmed up LSP client for nix
nixd LSP startup validated
📝 Note: LSP language selection is controlled by LSIF_ENABLED_LANGUAGES environment variable
```

### Successful Symbol Detection
After indexing, the export.json should contain:
- Nix function definitions
- Variable assignments
- Import statements
- File references
- Approximately 30+ symbols for a typical Nix project

### Log Output Patterns
Look for these patterns in debug logs:

```
DEBUG lsif_indexer::lsp::lsp_client] Attempting to create nixd LSP client with command: /nix/store/.../bin/nixd
DEBUG lsif_indexer::lsp::lsp_client] NIXD_PATH environment variable: Ok("/nix/store/.../bin/nixd")
INFO  lsif_indexer::lsp::lsp_pool] ✅ Successfully warmed up LSP client for nix
```

## Known Limitations

### 1. nixd LSP Server Limitations
- **Nix evaluation context**: nixd requires a valid Nix context to provide full functionality
- **Flake.nix dependencies**: Complex flake dependencies may affect symbol resolution
- **Performance**: Initial startup may be slower for large Nix projects

### 2. Environment-Specific Issues
- **Path resolution**: nixd path must be correctly resolved in the nix shell
- **LSP protocol version**: Ensure compatibility between nixd and the LSP client implementation
- **Resource constraints**: nixd may require sufficient memory for large projects

### 3. Testing Limitations
- **CI environment**: Some features may not work in headless CI environments
- **Nix evaluation**: Full evaluation may be limited without internet access or substitutes
- **Cross-platform**: Behavior may vary between different Nix installations

## Troubleshooting Common Issues

### Issue: "Failed to create LSP client"
**Symptoms**: LSP client creation fails with timeout or connection errors

**Solutions**:
1. Verify nixd is in PATH: `which nixd`
2. Check environment variables: `echo $NIXD_PATH`
3. Increase timeout in code (currently 5 seconds)
4. Run with debug logging: `RUST_LOG=debug`

### Issue: "nixd command not found"
**Symptoms**: nixd binary is not available in the environment

**Solutions**:
1. Ensure you're in nix develop shell: `nix develop`
2. Check flake.nix includes nixd in lspServers
3. Manually install nixd: `nix profile install github:nix-community/nixd`

### Issue: "No symbols detected"
**Symptoms**: LSP connects but no symbols are extracted

**Solutions**:
1. Verify Nix files exist in the project
2. Check LSP initialization parameters
3. Enable debug logging to see LSP communication
4. Verify nixd can evaluate the Nix code: `nixd --check file.nix`

### Issue: "Fallback indexer used instead of LSP"
**Symptoms**: System falls back to regex-based indexing

**Solutions**:
1. Check LSP warmup logs for errors
2. Verify LSIF_ENABLED_LANGUAGES includes "nix"
3. Ensure LSP timeout is sufficient
4. Test nixd manually outside the indexer

## Performance Expectations

### Startup Time
- **Cold start**: 2-5 seconds for nixd initialization
- **Warm start**: <1 second for subsequent operations
- **Large projects**: May take 10+ seconds for initial evaluation

### Memory Usage
- **Base nixd process**: 20-50 MB
- **With large flake**: 100-200 MB
- **Peak during indexing**: May spike to 300+ MB

### Symbol Detection Rate
- **Simple Nix files**: 95%+ symbol detection
- **Complex expressions**: 80-90% symbol detection
- **Generated code**: May have lower detection rates

## Verification Success Criteria

A successful nixd verification should demonstrate:

1. ✅ **nixd binary accessible** in nix development environment
2. ✅ **Environment variables properly set** (NIXD_PATH, etc.)
3. ✅ **LSP client creation succeeds** without timeouts
4. ✅ **LSP initialization handshake completes** successfully
5. ✅ **Symbol extraction works** on sample Nix files
6. ✅ **No fallback to regex indexer** when LSP should work
7. ✅ **Proper error handling** for edge cases
8. ✅ **Resource usage within expected bounds**

## Next Steps After Verification

Once verification passes:
1. Run full project indexing with nixd
2. Compare symbol count with fallback indexer
3. Test with various Nix file types (expressions, modules, flakes)
4. Benchmark performance against previous implementation
5. Document any project-specific configuration requirements

## Additional Resources

- [nixd Documentation](https://github.com/nix-community/nixd)
- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [Project NIXD_LSP_SPECIFICATION.md](./NIXD_LSP_SPECIFICATION.md)
- [Nix-only Mode Testing](./test_nix_only_mode.md)