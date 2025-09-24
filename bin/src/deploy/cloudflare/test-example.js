#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Example Integration Test Usage
 *
 * This script demonstrates how to use the comprehensive integration test suite
 * with various configurations and scenarios.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧪 R2 Connection Management System - Integration Test Examples');
console.log('='.repeat(70));
console.log();

const examples = [
  {
    name: 'Quick Validation',
    description: 'Fast validation for development workflow',
    command: 'TEST_CATEGORY=E2E_WORKFLOW,ENV_CONFIG node test-ci-runner.js',
    estimatedTime: '30-60 seconds'
  },
  {
    name: 'Security Focused',
    description: 'Security validation and compliance testing',
    command: 'TEST_CATEGORY=SECURITY node test-ci-runner.js',
    estimatedTime: '30-60 seconds'
  },
  {
    name: 'CLI Integration',
    description: 'Command-line interface and tool integration',
    command: 'TEST_CATEGORY=CLI_INTERFACE node test-ci-runner.js',
    estimatedTime: '60-120 seconds'
  },
  {
    name: 'Performance Benchmarks',
    description: 'Performance characteristics and regression detection',
    command: 'TEST_CATEGORY=PERFORMANCE node test-ci-runner.js',
    estimatedTime: '120-300 seconds'
  },
  {
    name: 'Complete Test Suite',
    description: 'Full comprehensive testing',
    command: 'node test-integration-comprehensive.js',
    estimatedTime: '5-10 minutes'
  },
  {
    name: 'CI-Ready with Artifacts',
    description: 'CI mode with JUnit output and artifacts',
    command: 'CI=true TEST_OUTPUT_FORMAT=junit GENERATE_TEST_ARTIFACTS=true node test-ci-runner.js',
    estimatedTime: '5-10 minutes'
  }
];

// Show examples
examples.forEach((example, index) => {
  console.log(`${index + 1}. ${example.name}`);
  console.log(`   ${example.description}`);
  console.log(`   Command: ${example.command}`);
  console.log(`   Time: ${example.estimatedTime}`);
  console.log();
});

// Check if user wants to run an example
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('Usage: node test-example.js <example_number>');
  console.log('Example: node test-example.js 1');
  console.log();
  console.log('Available examples:');
  examples.forEach((example, index) => {
    console.log(`  ${index + 1}: ${example.name}`);
  });
  process.exit(0);
}

const exampleNumber = parseInt(args[0]);

if (isNaN(exampleNumber) || exampleNumber < 1 || exampleNumber > examples.length) {
  console.error(`Invalid example number. Choose between 1 and ${examples.length}.`);
  process.exit(1);
}

const selectedExample = examples[exampleNumber - 1];

console.log(`🚀 Running: ${selectedExample.name}`);
console.log(`📋 Description: ${selectedExample.description}`);
console.log(`⏱️  Estimated time: ${selectedExample.estimatedTime}`);
console.log(`🔧 Command: ${selectedExample.command}`);
console.log();

try {
  console.log('▶️  Starting test execution...');
  console.log('-'.repeat(50));

  execSync(selectedExample.command, {
    stdio: 'inherit',
    cwd: process.cwd()
  });

  console.log('-'.repeat(50));
  console.log('✅ Test execution completed successfully!');

} catch (error) {
  console.log('-'.repeat(50));
  console.error('❌ Test execution failed!');
  console.error(`Exit code: ${error.status}`);
  process.exit(error.status || 1);
}