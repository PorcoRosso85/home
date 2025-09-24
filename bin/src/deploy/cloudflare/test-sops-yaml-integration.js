#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Integration test for shared SOPS YAML helper
 *
 * Tests the sops-yaml.js module with both generators to ensure
 * proper functionality, caching, error handling, and compatibility.
 */

const fs = require('fs');
const path = require('path');
const sopsYaml = require('./helpers/sops-yaml.js');

// Test configuration
const TEST_CONFIG = {
  verbose: process.argv.includes('--verbose'),
  skipSops: process.argv.includes('--skip-sops'),
  testCaching: process.argv.includes('--test-cache')
};

/**
 * Colored logging for test output
 */
function testLog(message, type = 'info') {
  const colors = {
    info: '\x1b[36m',    // Cyan
    success: '\x1b[32m', // Green
    warning: '\x1b[33m', // Yellow
    error: '\x1b[31m',   // Red
    reset: '\x1b[0m'
  };

  const prefix = {
    info: '🧪',
    success: '✅',
    warning: '⚠️ ',
    error: '❌'
  };

  console.log(`${colors[type]}${prefix[type]} ${message}${colors.reset}`);
}

/**
 * Test suite class
 */
class SOPSYamlTestSuite {
  constructor() {
    this.tests = [];
    this.passed = 0;
    this.failed = 0;
  }

  async runTest(name, testFn) {
    try {
      testLog(`Running: ${name}`, 'info');
      await testFn();
      this.passed++;
      testLog(`PASS: ${name}`, 'success');
    } catch (error) {
      this.failed++;
      testLog(`FAIL: ${name} - ${error.message}`, 'error');
      if (TEST_CONFIG.verbose) {
        console.error(error.stack);
      }
    }
  }

  showResults() {
    const total = this.passed + this.failed;
    testLog(`\nTest Results: ${this.passed}/${total} passed`,
             this.failed === 0 ? 'success' : 'warning');

    if (this.failed > 0) {
      testLog(`${this.failed} tests failed`, 'error');
      process.exit(1);
    }
  }
}

/**
 * Test basic module functionality
 */
async function testBasicFunctionality() {
  // Test module exports
  const expectedExports = [
    'decrypt', 'decryptWithValidation', 'getEnvironmentConfig',
    'decryptMultiple', 'clearCache', 'getCacheStats',
    'setLogLevel', 'healthCheck', 'schemas', 'CONFIG'
  ];

  for (const exportName of expectedExports) {
    if (!(exportName in sopsYaml)) {
      throw new Error(`Missing export: ${exportName}`);
    }
  }

  // Test configuration
  if (!sopsYaml.CONFIG || typeof sopsYaml.CONFIG !== 'object') {
    throw new Error('CONFIG export is invalid');
  }

  // Test schemas
  if (!sopsYaml.schemas.r2) {
    throw new Error('R2 schema is missing');
  }
}

/**
 * Test template mode functionality
 */
async function testTemplateMode() {
  // Test environment config with template
  const config = await sopsYaml.getEnvironmentConfig('r2', 'dev', true);

  if (!config.cf_account_id || !config.r2_buckets) {
    throw new Error('Template config missing required fields');
  }

  if (config.cf_account_id === 'your-account-id-here') {
    throw new Error('Template should not contain placeholder values');
  }

  testLog(`Template config: ${config.cf_account_id.substring(0, 10)}...`, 'info');
}

/**
 * Test caching functionality
 */
async function testCaching() {
  // Clear cache first
  sopsYaml.clearCache();
  let stats = sopsYaml.getCacheStats();

  if (stats.size !== 0) {
    throw new Error('Cache not properly cleared');
  }

  // Test cache miss and hit with template mode
  const config1 = await sopsYaml.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsYaml.getCacheStats();

  if (stats.misses !== 1) {
    throw new Error(`Expected 1 cache miss, got ${stats.misses}`);
  }

  const config2 = await sopsYaml.getEnvironmentConfig('r2', 'dev', true);
  stats = sopsYaml.getCacheStats();

  if (stats.hits !== 1) {
    throw new Error(`Expected 1 cache hit, got ${stats.hits}`);
  }

  // Configs should be identical
  if (JSON.stringify(config1) !== JSON.stringify(config2)) {
    throw new Error('Cached config differs from original');
  }

  testLog(`Cache stats: ${stats.hits} hits, ${stats.misses} misses`, 'info');
}

/**
 * Test error handling
 */
async function testErrorHandling() {
  // Test invalid environment
  try {
    await sopsYaml.getEnvironmentConfig('r2', 'invalid', false);
    throw new Error('Should have thrown for invalid environment');
  } catch (error) {
    if (!error.message.includes('Invalid environment')) {
      throw new Error(`Unexpected error message: ${error.message}`);
    }
  }

  // Test invalid config type
  try {
    await sopsYaml.getEnvironmentConfig('invalid', 'dev', true);
    throw new Error('Should have thrown for invalid config type');
  } catch (error) {
    if (!error.message.includes('No template available')) {
      throw new Error(`Unexpected error message: ${error.message}`);
    }
  }
}

/**
 * Test health check functionality
 */
async function testHealthCheck() {
  const health = await sopsYaml.healthCheck();

  if (!health.timestamp || !health.cache) {
    throw new Error('Health check missing required fields');
  }

  if (typeof health.sops !== 'boolean' ||
      typeof health.ageKey !== 'boolean' ||
      typeof health.sopsConfig !== 'boolean') {
    throw new Error('Health check boolean fields invalid');
  }

  testLog(`Health: SOPS=${health.sops}, Age=${health.ageKey}, Config=${health.sopsConfig}`, 'info');
}

/**
 * Test schema validation
 */
async function testSchemaValidation() {
  // Test with valid template config
  const config = await sopsYaml.decryptWithValidation(
    'nonexistent-test.yaml', // Won't be accessed in template mode
    sopsYaml.schemas.r2,
    { useTemplate: true, bypassCache: true }
  );

  if (!config.cf_account_id || !config.r2_buckets) {
    throw new Error('Schema validation failed for valid config');
  }
}

/**
 * Test generator integration (dry-run mode)
 */
async function testGeneratorIntegration() {
  // Test connection manifest generator
  try {
    const manifestGenerator = require('./scripts/gen-connection-manifest.js');

    if (!manifestGenerator.generateManifest || !manifestGenerator.CONFIG) {
      throw new Error('Connection manifest generator missing expected exports');
    }

    testLog('Connection manifest generator integration verified', 'info');
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      testLog('Connection manifest generator not found (expected in some setups)', 'warning');
    } else {
      throw error;
    }
  }

  // Test wrangler config generator
  try {
    const wranglerGenerator = require('./scripts/gen-wrangler-config.js');

    if (!wranglerGenerator.generateWranglerConfig || !wranglerGenerator.CONFIG) {
      throw new Error('Wrangler config generator missing expected exports');
    }

    testLog('Wrangler config generator integration verified', 'info');
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      testLog('Wrangler config generator not found (expected in some setups)', 'warning');
    } else {
      throw error;
    }
  }
}

/**
 * Test file operations and path handling
 */
async function testFileOperations() {
  // Test path expansion
  const expandedPath = sopsYaml.expandPath('~/test');
  const homePath = process.env.HOME || '/tmp';

  if (!expandedPath.startsWith(homePath)) {
    throw new Error('Path expansion failed');
  }

  // Test internal functions if available
  if (sopsYaml._internal) {
    const cacheKey = sopsYaml._internal.generateCacheKey('/test/file.yaml', { option: 'value' });
    if (!cacheKey || typeof cacheKey !== 'string') {
      throw new Error('Cache key generation failed');
    }
  }
}

/**
 * Test logging levels
 */
async function testLogging() {
  // Test different log levels
  const levels = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'];

  for (const level of levels) {
    sopsYaml.setLogLevel(level);
    // No error should be thrown
  }

  // Test invalid log level
  try {
    sopsYaml.setLogLevel('INVALID');
    throw new Error('Should have thrown for invalid log level');
  } catch (error) {
    if (!error.message.includes('Invalid log level')) {
      throw new Error(`Unexpected error message: ${error.message}`);
    }
  }

  // Reset to default
  sopsYaml.setLogLevel('INFO');
}

/**
 * Main test execution
 */
async function main() {
  testLog('Starting SOPS YAML Helper Integration Tests', 'info');
  testLog(`Configuration: verbose=${TEST_CONFIG.verbose}, skipSops=${TEST_CONFIG.skipSops}`, 'info');

  const suite = new SOPSYamlTestSuite();

  // Run basic tests
  await suite.runTest('Basic Functionality', testBasicFunctionality);
  await suite.runTest('Template Mode', testTemplateMode);
  await suite.runTest('Error Handling', testErrorHandling);
  await suite.runTest('Health Check', testHealthCheck);
  await suite.runTest('Schema Validation', testSchemaValidation);
  await suite.runTest('File Operations', testFileOperations);
  await suite.runTest('Logging Levels', testLogging);
  await suite.runTest('Generator Integration', testGeneratorIntegration);

  // Optional caching test
  if (TEST_CONFIG.testCaching) {
    await suite.runTest('Caching Functionality', testCaching);
  }

  suite.showResults();
  testLog('All tests completed successfully!', 'success');
}

// Help message
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
SOPS YAML Helper Integration Tests

Usage: node test-sops-yaml-integration.js [OPTIONS]

Options:
  --verbose      Show detailed error messages and stack traces
  --skip-sops    Skip tests that require SOPS setup
  --test-cache   Include caching functionality tests
  --help, -h     Show this help message

Examples:
  node test-sops-yaml-integration.js
  node test-sops-yaml-integration.js --verbose --test-cache
  `);
  process.exit(0);
}

// Run tests
main().catch(error => {
  testLog(`Test suite failed: ${error.message}`, 'error');
  if (TEST_CONFIG.verbose) {
    console.error(error.stack);
  }
  process.exit(1);
});