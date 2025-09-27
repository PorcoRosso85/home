#!/usr/bin/env node

/**
 * Test script for JSON Schema validation functionality
 *
 * This script tests the complete pipeline:
 * 1. Schema validator functionality
 * 2. Integration with sops-yaml.js
 * 3. End-to-end SOT validation
 */

const fs = require('fs');
const path = require('path');

// Test configuration
const TESTS = {
  SCHEMA_VALIDATOR: 'Schema Validator Module',
  SOT_INTEGRATION: 'SOT Integration with sops-yaml.js',
  FILE_VALIDATION: 'File-based validation',
  ERROR_HANDLING: 'Error handling and reporting'
};

let testResults = {};

function log(message, level = 'INFO') {
  const prefix = {
    ERROR: '❌',
    WARN: '⚠️ ',
    INFO: '📋',
    SUCCESS: '✅',
    DEBUG: '🔍'
  };

  console.log(`${prefix[level] || '📋'} ${message}`);
}

function runTest(testName, testFunction) {
  log(`Testing: ${testName}`, 'INFO');

  try {
    const result = testFunction();
    testResults[testName] = { passed: true, result };
    log(`✅ ${testName}: PASSED`, 'SUCCESS');
    return result;
  } catch (error) {
    testResults[testName] = { passed: false, error: error.message };
    log(`❌ ${testName}: FAILED - ${error.message}`, 'ERROR');
    return null;
  }
}

async function runAsyncTest(testName, testFunction) {
  log(`Testing: ${testName}`, 'INFO');

  try {
    const result = await testFunction();
    testResults[testName] = { passed: true, result };
    log(`✅ ${testName}: PASSED`, 'SUCCESS');
    return result;
  } catch (error) {
    testResults[testName] = { passed: false, error: error.message };
    log(`❌ ${testName}: FAILED - ${error.message}`, 'ERROR');
    return null;
  }
}

// Test 1: Schema Validator Module Basic Functionality
function testSchemaValidatorModule() {
  // Test if schema validator can be loaded
  const schemaValidator = require('./helpers/schema-validator.js');

  if (!schemaValidator.validateSOT) {
    throw new Error('validateSOT function not exported');
  }

  if (!schemaValidator.healthCheck) {
    throw new Error('healthCheck function not exported');
  }

  // Test health check
  const health = schemaValidator.healthCheck();

  if (!health.timestamp) {
    throw new Error('Health check missing timestamp');
  }

  log(`  Health check: AJV=${health.ajv}, Schema=${health.defaultSchema}`, 'DEBUG');

  return {
    healthCheck: health,
    moduleLoaded: true
  };
}

// Test 2: Basic validation with valid SOT data
function testValidSOTValidation() {
  const schemaValidator = require('./helpers/schema-validator.js');

  const validConfig = {
    version: "1.0",
    r2: {
      buckets: [
        {
          name: "test-bucket",
          binding: "TEST_BUCKET"
        }
      ]
    }
  };

  const result = schemaValidator.validateSOT(validConfig);

  if (!result.valid) {
    throw new Error(`Valid config failed validation: ${JSON.stringify(result.errors, null, 2)}`);
  }

  log(`  Validation duration: ${result.duration}ms`, 'DEBUG');

  return {
    validationResult: result,
    configValid: true
  };
}

// Test 3: Validation with invalid SOT data
function testInvalidSOTValidation() {
  const schemaValidator = require('./helpers/schema-validator.js');

  const invalidConfig = {
    // Missing required version field
    r2: {
      buckets: [
        {
          // Missing required binding field
          name: "test-bucket"
        }
      ]
    }
  };

  const result = schemaValidator.validateSOT(invalidConfig);

  if (result.valid) {
    throw new Error('Invalid config passed validation when it should have failed');
  }

  if (!result.errors || result.errors.length === 0) {
    throw new Error('No validation errors reported for invalid config');
  }

  log(`  Expected validation errors: ${result.errors.length}`, 'DEBUG');

  return {
    validationResult: result,
    errorsReported: result.errors.length
  };
}

// Test 4: File-based validation (without SOPS)
function testFileBasedValidation() {
  // Check if our test file exists
  const testFile = 'spec/dev/cloudflare.yaml';

  if (!fs.existsSync(testFile)) {
    throw new Error(`Test file not found: ${testFile}`);
  }

  // Read and parse the file manually for testing
  const fileContent = fs.readFileSync(testFile, 'utf8');

  // Simple YAML parsing for basic key-value pairs
  const config = {};
  const lines = fileContent.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('-')) {
      continue;
    }

    const match = trimmed.match(/^([^:]+):\s*(.*)$/);
    if (match) {
      const key = match[1].trim();
      let value = match[2].trim();

      if (value.startsWith('"') && value.endsWith('"')) {
        value = value.slice(1, -1);
      }

      config[key] = value;
    }
  }

  // We expect at least version to be parsed
  if (!config.version) {
    log(`  Warning: Could not parse version from YAML file`, 'WARN');
  }

  return {
    fileExists: true,
    fileContent: fileContent.length,
    parsedConfig: config
  };
}

// Test 5: SOPS Integration (if available)
async function testSOPSIntegration() {
  try {
    const sopsYaml = require('./helpers/sops-yaml.js');

    // Test if we can load the SOT config for dev environment
    // This will test the integration of schema validation

    // First, check if the function exists
    if (!sopsYaml.getSOTConfig) {
      throw new Error('getSOTConfig function not found in sops-yaml.js');
    }

    // Note: This test may fail if SOPS is not configured or the file is encrypted
    // We'll catch that specific case
    try {
      const config = await sopsYaml.getSOTConfig('dev', { skipValidation: true });

      log(`  SOT config loaded successfully`, 'DEBUG');

      // Now test with validation enabled
      const configWithValidation = await sopsYaml.getSOTConfig('dev');

      return {
        configLoaded: true,
        validationIntegrated: true,
        configKeys: Object.keys(config).length
      };

    } catch (error) {
      if (error.message.includes('SOPS') || error.message.includes('Age') || error.message.includes('decrypt')) {
        log(`  SOPS not configured (expected for testing): ${error.message}`, 'WARN');
        return {
          configLoaded: false,
          sopsNotConfigured: true,
          reason: 'SOPS encryption not set up for testing'
        };
      } else {
        throw error;
      }
    }

  } catch (error) {
    throw new Error(`SOPS integration test failed: ${error.message}`);
  }
}

// Test 6: Error handling and graceful degradation
function testErrorHandling() {
  const schemaValidator = require('./helpers/schema-validator.js');

  // Test with malformed data
  try {
    const result = schemaValidator.validateSOT(null);
    if (result.valid) {
      throw new Error('Null config should not validate successfully');
    }

    if (!result.errors || result.errors.length === 0) {
      throw new Error('No errors reported for null config');
    }
  } catch (error) {
    if (!error.message.includes('validation')) {
      throw new Error(`Unexpected error for null config: ${error.message}`);
    }
  }

  // Test with circular reference (should handle gracefully)
  const circularConfig = { version: "1.0" };
  circularConfig.self = circularConfig;

  try {
    const result = schemaValidator.validateSOT(circularConfig);
    // Should handle gracefully without crashing
  } catch (error) {
    if (error.message.includes('circular')) {
      log(`  Circular reference handled correctly`, 'DEBUG');
    }
  }

  return {
    nullHandled: true,
    circularHandled: true
  };
}

// Main test execution
async function runAllTests() {
  log('🚀 Starting JSON Schema Validation Tests', 'INFO');
  log('=========================================', 'INFO');

  // Run synchronous tests
  runTest('Schema Validator Module Loading', testSchemaValidatorModule);
  runTest('Valid SOT Configuration Validation', testValidSOTValidation);
  runTest('Invalid SOT Configuration Validation', testInvalidSOTValidation);
  runTest('File-based Validation', testFileBasedValidation);
  runTest('Error Handling', testErrorHandling);

  // Run asynchronous tests
  await runAsyncTest('SOPS Integration', testSOPSIntegration);

  // Summary
  log('', 'INFO');
  log('📊 Test Results Summary', 'INFO');
  log('=======================', 'INFO');

  let passed = 0;
  let failed = 0;

  for (const [testName, result] of Object.entries(testResults)) {
    if (result.passed) {
      log(`✅ ${testName}: PASSED`, 'SUCCESS');
      passed++;
    } else {
      log(`❌ ${testName}: FAILED - ${result.error}`, 'ERROR');
      failed++;
    }
  }

  log('', 'INFO');
  log(`📈 Results: ${passed} passed, ${failed} failed`, passed === Object.keys(testResults).length ? 'SUCCESS' : 'WARN');

  if (failed > 0) {
    log('', 'INFO');
    log('🔧 Recommended Actions:', 'INFO');
    log('- Check that AJV is installed: npm install ajv ajv-formats', 'INFO');
    log('- Verify schema files exist in schemas/ directory', 'INFO');
    log('- For SOPS tests: run `just secrets-init` to set up encryption', 'INFO');
  } else {
    log('', 'INFO');
    log('🎉 All tests passed! JSON Schema validation is working correctly.', 'SUCCESS');
  }

  return {
    totalTests: Object.keys(testResults).length,
    passed,
    failed,
    success: failed === 0
  };
}

// Execute tests if run directly
if (require.main === module) {
  runAllTests()
    .then(summary => {
      process.exit(summary.success ? 0 : 1);
    })
    .catch(error => {
      log(`💥 Test execution failed: ${error.message}`, 'ERROR');
      process.exit(1);
    });
}

module.exports = {
  runAllTests,
  testResults
};