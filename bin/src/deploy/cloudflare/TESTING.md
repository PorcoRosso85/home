# R2 Connection Management System - Testing Guide

This document provides comprehensive guidance for testing the R2 Connection Management System, including setup, execution, and customization of the integration test suite.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [CI/CD Integration](#cicd-integration)
- [Test Configuration](#test-configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

The testing framework provides comprehensive validation of the R2 connection management system through multiple test categories:

- **End-to-End Workflow Tests**: Complete secrets → manifest → validation workflows
- **Environment Configuration Tests**: Multi-environment (dev/stg/prod) validation
- **AWS SDK v3 Compatibility Tests**: S3Client compatibility verification
- **SOPS Encryption Tests**: Encryption/decryption workflow validation
- **CLI Interface Tests**: Command-line tool integration testing
- **Security Validation Tests**: Security posture and vulnerability testing
- **Performance Benchmarks**: Performance characteristics and regression detection
- **Error Scenario Tests**: Comprehensive error handling validation

## 🚀 Quick Start

### Prerequisites

```bash
# Required
node >= 16.0.0
just (command runner)

# Optional (enables additional tests)
nix (package manager)
sops (secret encryption)
age (encryption keys)
```

### Basic Test Execution

```bash
# Run all tests
node test-integration-comprehensive.js

# Run with verbose output
node test-integration-comprehensive.js --verbose

# Run specific categories
TEST_CATEGORY=E2E_WORKFLOW,SECURITY node test-integration-comprehensive.js

# Skip SOPS tests (if SOPS not configured)
node test-integration-comprehensive.js --skip-sops
```

### CI-Ready Execution

```bash
# CI mode with JUnit output
CI=true TEST_OUTPUT_FORMAT=junit node test-ci-runner.js

# Parallel execution
TEST_PARALLEL=true node test-ci-runner.js

# Generate artifacts
GENERATE_TEST_ARTIFACTS=true node test-ci-runner.js
```

## 📊 Test Categories

### E2E_WORKFLOW
**Purpose**: Validates complete end-to-end workflows
**Tests**: Template workflows, multi-environment processing, encrypted workflows
**Duration**: ~30-60 seconds
**Prerequisites**: Basic system setup

```bash
# Run only workflow tests
TEST_CATEGORY=E2E_WORKFLOW node test-ci-runner.js
```

### ENV_CONFIG
**Purpose**: Validates environment-specific configurations
**Tests**: Dev/staging/production isolation, configuration inheritance
**Duration**: ~20-40 seconds
**Prerequisites**: Basic system setup

```bash
# Test environment configurations
TEST_CATEGORY=ENV_CONFIG node test-ci-runner.js
```

### AWS_SDK_COMPAT
**Purpose**: Validates AWS SDK v3 S3Client compatibility
**Tests**: Configuration generation, credential validation, endpoint setup
**Duration**: ~15-30 seconds
**Prerequisites**: Node.js with AWS SDK v3 (optional)

```bash
# Test AWS SDK compatibility
TEST_CATEGORY=AWS_SDK_COMPAT node test-ci-runner.js
```

### SOPS_ENCRYPTION
**Purpose**: Validates SOPS encryption/decryption workflows
**Tests**: Age key management, encryption operations, cache behavior
**Duration**: ~45-90 seconds
**Prerequisites**: SOPS binary, age keys configured

```bash
# Test SOPS encryption (requires setup)
TEST_CATEGORY=SOPS_ENCRYPTION node test-ci-runner.js

# Skip SOPS tests if not configured
SKIP_SOPS_TESTS=true node test-ci-runner.js
```

### CLI_INTERFACE
**Purpose**: Validates command-line interfaces and integration
**Tests**: Just tasks, Nix apps, script interfaces, error handling
**Duration**: ~60-120 seconds
**Prerequisites**: just command runner, nix (optional)

```bash
# Test CLI interfaces
TEST_CATEGORY=CLI_INTERFACE node test-ci-runner.js
```

### SECURITY
**Purpose**: Validates security measures and compliance
**Tests**: Plaintext detection, permissions, attack surface analysis
**Duration**: ~30-60 seconds
**Prerequisites**: Basic system setup

```bash
# Run security validation
TEST_CATEGORY=SECURITY node test-ci-runner.js
```

### PERFORMANCE
**Purpose**: Benchmarks performance characteristics
**Tests**: Execution speed, memory usage, cache efficiency, scalability
**Duration**: ~120-300 seconds
**Prerequisites**: Basic system setup

```bash
# Run performance benchmarks
TEST_CATEGORY=PERFORMANCE node test-ci-runner.js

# Skip slow performance tests
SKIP_SLOW_TESTS=true node test-ci-runner.js
```

### ERROR_SCENARIOS
**Purpose**: Validates comprehensive error handling
**Tests**: File system errors, invalid inputs, resource exhaustion
**Duration**: ~90-180 seconds
**Prerequisites**: Basic system setup

```bash
# Test error scenarios
TEST_CATEGORY=ERROR_SCENARIOS node test-ci-runner.js
```

## 🔧 Running Tests

### Local Development

```bash
# Basic execution
npm test
# or
just test

# Verbose output for debugging
npm run test:verbose
# or
node test-integration-comprehensive.js --verbose

# Specific test modules
node test-modules/workflow-integration.js
node test-modules/security-validation.js
```

### Development Workflow

```bash
# 1. Run quick validation
TEST_CATEGORY=E2E_WORKFLOW,ENV_CONFIG node test-ci-runner.js

# 2. Run security checks
TEST_CATEGORY=SECURITY node test-ci-runner.js

# 3. Full test suite
node test-integration-comprehensive.js

# 4. Performance validation (if needed)
TEST_CATEGORY=PERFORMANCE node test-ci-runner.js
```

### Production Validation

```bash
# Complete validation before deployment
CI=true GENERATE_TEST_ARTIFACTS=true node test-ci-runner.js

# Production-focused tests
TEST_CATEGORY=SECURITY,E2E_WORKFLOW node test-ci-runner.js
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm ci

    - name: Run integration tests
      run: |
        CI=true \
        TEST_OUTPUT_FORMAT=junit \
        TEST_OUTPUT_FILE=test-results.xml \
        GENERATE_TEST_ARTIFACTS=true \
        node test-ci-runner.js

    - name: Upload test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results
        path: |
          test-results.xml
          test-artifacts/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                script {
                    sh '''
                        CI=true \
                        TEST_OUTPUT_FORMAT=junit \
                        TEST_OUTPUT_FILE=test-results.xml \
                        GENERATE_TEST_ARTIFACTS=true \
                        node test-ci-runner.js
                    '''
                }
            }

            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'test-artifacts/**/*', allowEmptyArchive: true
                }
            }
        }
    }
}
```

### GitLab CI

```yaml
test:
  stage: test
  image: node:18
  script:
    - npm ci
    - |
      CI=true \
      TEST_OUTPUT_FORMAT=junit \
      TEST_OUTPUT_FILE=test-results.xml \
      GENERATE_TEST_ARTIFACTS=true \
      node test-ci-runner.js
  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - test-artifacts/
    when: always
```

## ⚙️ Test Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `TEST_OUTPUT_FORMAT` | Output format | `console` | `junit`, `tap`, `json` |
| `TEST_OUTPUT_FILE` | Output file path | none | `test-results.xml` |
| `TEST_CATEGORY` | Categories to run | all | `E2E_WORKFLOW,SECURITY` |
| `SKIP_SLOW_TESTS` | Skip slow categories | `false` | `true` |
| `SKIP_SOPS_TESTS` | Skip SOPS tests | `false` | `true` |
| `TEST_TIMEOUT` | Global timeout (ms) | `1800000` | `3600000` |
| `INDIVIDUAL_TEST_TIMEOUT` | Per-test timeout (ms) | `120000` | `60000` |
| `TEST_PARALLEL` | Parallel execution | `false` | `true` |
| `MAX_PARALLEL_TESTS` | Max parallel categories | `4` | `8` |
| `GENERATE_TEST_ARTIFACTS` | Generate artifacts | `false` | `true` |
| `TEST_ARTIFACTS_DIR` | Artifacts directory | `./test-artifacts` | `./reports` |
| `RETRY_FAILED_TESTS` | Retry failures | `false` | `true` |
| `MAX_TEST_RETRIES` | Max retry attempts | `2` | `3` |

### Configuration Examples

```bash
# Fast feedback loop
TEST_CATEGORY=E2E_WORKFLOW INDIVIDUAL_TEST_TIMEOUT=30000 node test-ci-runner.js

# Comprehensive CI testing
CI=true \
TEST_PARALLEL=true \
GENERATE_TEST_ARTIFACTS=true \
RETRY_FAILED_TESTS=true \
node test-ci-runner.js

# Development with SOPS
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt node test-integration-comprehensive.js

# Security-focused testing
TEST_CATEGORY=SECURITY,ERROR_SCENARIOS \
GENERATE_TEST_ARTIFACTS=true \
node test-ci-runner.js
```

### SOPS Configuration

For full testing capabilities, configure SOPS encryption:

```bash
# 1. Install SOPS and age
nix-env -iA nixpkgs.sops nixpkgs.age
# or
brew install sops age

# 2. Generate age key
age-keygen -o ~/.config/sops/age/keys.txt

# 3. Configure SOPS
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt

# 4. Update .sops.yaml with your public key
# (Get public key from the generated file)
```

## 🎯 Output Formats

### Console Output (Default)
Human-readable output with colors and progress indicators.

```bash
node test-integration-comprehensive.js
```

### TAP (Test Anything Protocol)
Machine-readable format supported by many test runners.

```bash
TEST_OUTPUT_FORMAT=tap node test-ci-runner.js
```

### JUnit XML
Standard format for CI systems like Jenkins, GitHub Actions.

```bash
TEST_OUTPUT_FORMAT=junit TEST_OUTPUT_FILE=results.xml node test-ci-runner.js
```

### JSON Report
Structured format with detailed test information.

```bash
TEST_OUTPUT_FORMAT=json TEST_OUTPUT_FILE=report.json node test-ci-runner.js
```

## 📋 Test Artifacts

When `GENERATE_TEST_ARTIFACTS=true`, the following artifacts are created:

- **performance-report.json**: Performance metrics and benchmarks
- **error-report.json**: Detailed error information for failed tests
- **environment-snapshot.json**: Complete environment and configuration snapshot
- **coverage files**: Code coverage reports (if available)

## 🔍 Troubleshooting

### Common Issues

#### 1. SOPS Tests Failing
```bash
# Check SOPS installation
sops --version

# Check age key configuration
echo $SOPS_AGE_KEY_FILE
test -f $SOPS_AGE_KEY_FILE && echo "Age key file exists"

# Skip SOPS tests if not configured
SKIP_SOPS_TESTS=true node test-ci-runner.js
```

#### 2. Permission Errors
```bash
# Check file permissions
ls -la test-modules/
ls -la scripts/

# Fix executable permissions
chmod +x test-integration-comprehensive.js
chmod +x test-ci-runner.js
chmod +x scripts/*.js
```

#### 3. Timeout Issues
```bash
# Increase timeouts
INDIVIDUAL_TEST_TIMEOUT=300000 node test-ci-runner.js

# Skip slow tests
SKIP_SLOW_TESTS=true node test-ci-runner.js

# Run specific categories
TEST_CATEGORY=E2E_WORKFLOW node test-ci-runner.js
```

#### 4. Memory Issues
```bash
# Increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=4096" node test-ci-runner.js

# Run tests sequentially
TEST_PARALLEL=false node test-ci-runner.js
```

### Debug Mode

```bash
# Enable verbose logging
node test-integration-comprehensive.js --verbose

# Debug specific test module
DEBUG=1 node test-modules/workflow-integration.js

# CI debug mode
DEBUG=1 CI=true node test-ci-runner.js
```

### Test Isolation

```bash
# Run single test category
TEST_CATEGORY=SECURITY node test-ci-runner.js

# Clean environment
just clean
rm -rf test-artifacts/
node test-integration-comprehensive.js
```

## 🤝 Contributing

### Adding New Tests

1. **Create test module**: Add to `test-modules/` directory
2. **Follow naming convention**: `category-name.js`
3. **Export runTests function**: `module.exports = { runTests }`
4. **Update test runner**: Add category to `test-ci-runner.js`
5. **Document**: Update this guide

### Test Module Template

```javascript
/**
 * New Test Category
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running New Test Category...');

  await testSuite.runTest('Test Name', async () => {
    // Test implementation
  }, { category: 'NEW_CATEGORY' });
}

module.exports = {
  runTests,
};
```

### Best Practices

- **Isolation**: Tests should not depend on external state
- **Cleanup**: Always clean up temporary files and resources
- **Error Handling**: Provide meaningful error messages
- **Performance**: Keep tests reasonably fast
- **Documentation**: Document test purpose and requirements

### Running Tests During Development

```bash
# Quick validation
TEST_CATEGORY=E2E_WORKFLOW,ENV_CONFIG node test-ci-runner.js

# Full validation before commit
node test-integration-comprehensive.js

# Performance impact check
TEST_CATEGORY=PERFORMANCE node test-ci-runner.js
```

## 📖 Additional Resources

- [Integration Test Source](./test-integration-comprehensive.js)
- [CI Runner Source](./test-ci-runner.js)
- [Test Modules](./test-modules/)
- [Security Policy](./SECURITY-POLICY.md)
- [Project README](./README.md)

---

For questions or issues with testing, please check the troubleshooting section above or create an issue with detailed logs and environment information.