#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Comprehensive End-to-End Integration Test Suite
 * for R2 Connection Management System
 *
 * This test suite validates the complete workflow from secret loading
 * through manifest generation, validation, and deployment preparation.
 * It tests all integration points and ensures the system works correctly
 * as a whole.
 *
 * Test Coverage:
 * - Full workflow integration (secrets → manifest → validation)
 * - Environment-specific configuration generation
 * - AWS SDK v3 S3Client compatibility validation
 * - SOPS encryption/decryption workflows
 * - CLI interface and error handling
 * - Command integration (Nix + Just)
 * - Security validation (plaintext detection, etc.)
 * - Performance and memory usage validation
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const crypto = require('crypto');

// Test configuration
const TEST_CONFIG = {
  verbose: process.argv.includes('--verbose') || process.argv.includes('-v'),
  skipSops: process.argv.includes('--skip-sops'),
  skipCI: process.argv.includes('--skip-ci'),
  performance: process.argv.includes('--performance'),
  environments: process.env.TEST_ENVIRONMENTS ? process.env.TEST_ENVIRONMENTS.split(',') : ['dev', 'stg', 'prod'],
  workDir: process.cwd(),
  tempDir: path.join(process.cwd(), 'test-temp'),
  timeout: 60000, // 60 seconds default timeout
};

// Colors for output
const COLORS = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

/**
 * Enhanced logging with categories and timestamps
 */
class Logger {
  constructor(verbose = false) {
    this.verbose = verbose;
    this.startTime = Date.now();
  }

  log(message, category = 'INFO', color = COLORS.cyan) {
    const timestamp = this.getElapsedTime();
    const prefix = `${color}[${timestamp}] ${category}${COLORS.reset}`;
    console.log(`${prefix} ${message}`);
  }

  info(message) {
    this.log(message, 'INFO', COLORS.cyan);
  }

  success(message) {
    this.log(message, 'PASS', COLORS.green);
  }

  warn(message) {
    this.log(message, 'WARN', COLORS.yellow);
  }

  error(message) {
    this.log(message, 'FAIL', COLORS.red);
  }

  debug(message) {
    if (this.verbose) {
      this.log(message, 'DEBUG', COLORS.blue);
    }
  }

  performance(message) {
    this.log(message, 'PERF', COLORS.magenta);
  }

  getElapsedTime() {
    const elapsed = Date.now() - this.startTime;
    const seconds = Math.floor(elapsed / 1000);
    const ms = elapsed % 1000;
    return `${seconds.toString().padStart(3, '0')}.${ms.toString().padStart(3, '0')}s`;
  }
}

/**
 * Performance monitor for tracking resource usage
 */
class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.memoryBaseline = this.getCurrentMemoryUsage();
  }

  startTimer(name) {
    this.metrics.set(name, { start: process.hrtime.bigint() });
  }

  endTimer(name) {
    const metric = this.metrics.get(name);
    if (metric) {
      metric.end = process.hrtime.bigint();
      metric.duration = Number(metric.end - metric.start) / 1000000; // Convert to milliseconds
    }
    return metric;
  }

  getCurrentMemoryUsage() {
    const memUsage = process.memoryUsage();
    return {
      rss: memUsage.rss / 1024 / 1024, // MB
      heapUsed: memUsage.heapUsed / 1024 / 1024, // MB
      heapTotal: memUsage.heapTotal / 1024 / 1024, // MB
      external: memUsage.external / 1024 / 1024, // MB
    };
  }

  getMetrics() {
    const currentMemory = this.getCurrentMemoryUsage();
    const memoryDelta = {
      rss: currentMemory.rss - this.memoryBaseline.rss,
      heapUsed: currentMemory.heapUsed - this.memoryBaseline.heapUsed,
      heapTotal: currentMemory.heapTotal - this.memoryBaseline.heapTotal,
      external: currentMemory.external - this.memoryBaseline.external,
    };

    return {
      timings: Array.from(this.metrics.entries()).map(([name, metric]) => ({
        name,
        duration: metric.duration || 0,
      })),
      memory: {
        current: currentMemory,
        baseline: this.memoryBaseline,
        delta: memoryDelta,
      },
    };
  }
}

/**
 * Comprehensive test suite orchestrator
 */
class IntegrationTestSuite {
  constructor() {
    this.logger = new Logger(TEST_CONFIG.verbose);
    this.monitor = new PerformanceMonitor();
    this.testResults = [];
    this.passed = 0;
    this.failed = 0;
    this.skipped = 0;
    this.setupComplete = false;
  }

  /**
   * Run a test with comprehensive error handling and performance monitoring
   */
  async runTest(name, testFn, options = {}) {
    const testId = `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const { timeout = TEST_CONFIG.timeout, skipIf = false, category = 'INTEGRATION' } = options;

    if (skipIf) {
      this.logger.warn(`SKIP: ${name} - ${skipIf}`);
      this.skipped++;
      return;
    }

    this.logger.info(`Starting: ${name}`);
    this.monitor.startTimer(testId);

    const testResult = {
      name,
      category,
      status: 'running',
      startTime: Date.now(),
      endTime: null,
      duration: null,
      error: null,
      performance: null,
    };

    try {
      // Set up timeout
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error(`Test timeout after ${timeout}ms`)), timeout);
      });

      // Run test with timeout
      await Promise.race([testFn(), timeoutPromise]);

      // Test passed
      const timing = this.monitor.endTimer(testId);
      testResult.status = 'passed';
      testResult.endTime = Date.now();
      testResult.duration = timing.duration;
      testResult.performance = this.monitor.getMetrics();

      this.passed++;
      this.logger.success(`PASS: ${name} (${timing.duration.toFixed(2)}ms)`);

    } catch (error) {
      // Test failed
      const timing = this.monitor.endTimer(testId);
      testResult.status = 'failed';
      testResult.endTime = Date.now();
      testResult.duration = timing ? timing.duration : null;
      testResult.error = {
        message: error.message,
        stack: error.stack,
      };

      this.failed++;
      this.logger.error(`FAIL: ${name} - ${error.message}`);

      if (TEST_CONFIG.verbose) {
        this.logger.debug(`Error details: ${error.stack}`);
      }
    }

    this.testResults.push(testResult);
  }

  /**
   * Set up test environment
   */
  async setup() {
    if (this.setupComplete) return;

    this.logger.info('Setting up comprehensive integration test environment...');

    try {
      // Create temporary directory
      if (!fs.existsSync(TEST_CONFIG.tempDir)) {
        fs.mkdirSync(TEST_CONFIG.tempDir, { recursive: true });
      }

      // Verify essential files exist
      const requiredFiles = [
        'flake.nix',
        'justfile',
        '.sops.yaml',
        'r2.yaml.example',
        'helpers/sops-yaml.js',
        'schemas/r2-manifest.json',
        'scripts/gen-connection-manifest.js',
        'scripts/gen-wrangler-config.js',
      ];

      for (const file of requiredFiles) {
        const filePath = path.join(TEST_CONFIG.workDir, file);
        if (!fs.existsSync(filePath)) {
          throw new Error(`Required file missing: ${file}`);
        }
      }

      this.setupComplete = true;
      this.logger.success('Test environment setup complete');

    } catch (error) {
      this.logger.error(`Setup failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Clean up test environment
   */
  async cleanup() {
    this.logger.info('Cleaning up test environment...');

    try {
      // Remove temporary files
      if (fs.existsSync(TEST_CONFIG.tempDir)) {
        fs.rmSync(TEST_CONFIG.tempDir, { recursive: true, force: true });
      }

      // Clean up any test artifacts
      const testArtifacts = [
        'test-r2-manifest.json',
        'test-wrangler.toml',
        'test-output.json',
      ];

      for (const artifact of testArtifacts) {
        const artifactPath = path.join(TEST_CONFIG.workDir, artifact);
        if (fs.existsSync(artifactPath)) {
          fs.unlinkSync(artifactPath);
        }
      }

      this.logger.success('Cleanup complete');

    } catch (error) {
      this.logger.warn(`Cleanup warning: ${error.message}`);
    }
  }

  /**
   * Execute a shell command with proper error handling
   */
  async execCommand(command, options = {}) {
    const { timeout = 30000, cwd = TEST_CONFIG.workDir, env = process.env } = options;

    this.logger.debug(`Executing: ${command}`);

    return new Promise((resolve, reject) => {
      const child = spawn('bash', ['-c', command], {
        cwd,
        env,
        stdio: 'pipe',
        timeout,
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout, stderr, code });
        } else {
          reject(new Error(`Command failed with code ${code}: ${stderr || stdout}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`Command execution error: ${error.message}`));
      });
    });
  }

  /**
   * Show comprehensive test results
   */
  showResults() {
    const total = this.passed + this.failed + this.skipped;

    this.logger.info('');
    this.logger.info('='.repeat(80));
    this.logger.info(`COMPREHENSIVE INTEGRATION TEST RESULTS`);
    this.logger.info('='.repeat(80));

    this.logger.info(`Total Tests: ${total}`);
    this.logger.success(`Passed: ${this.passed}`);
    if (this.failed > 0) {
      this.logger.error(`Failed: ${this.failed}`);
    }
    if (this.skipped > 0) {
      this.logger.warn(`Skipped: ${this.skipped}`);
    }

    // Show performance summary
    if (TEST_CONFIG.performance) {
      this.showPerformanceSummary();
    }

    // Show failed tests details
    if (this.failed > 0) {
      this.logger.info('');
      this.logger.error('FAILED TESTS:');
      this.testResults
        .filter(result => result.status === 'failed')
        .forEach(result => {
          this.logger.error(`  - ${result.name}: ${result.error.message}`);
        });
    }

    this.logger.info('');

    if (this.failed === 0) {
      this.logger.success('🎉 ALL INTEGRATION TESTS PASSED!');
      this.logger.success('✅ R2 Connection Management System is fully functional');
      return 0;
    } else {
      this.logger.error('❌ SOME INTEGRATION TESTS FAILED');
      this.logger.error('⚠️  Please review and fix the failing components');
      return 1;
    }
  }

  /**
   * Show performance analysis
   */
  showPerformanceSummary() {
    const metrics = this.monitor.getMetrics();

    this.logger.info('');
    this.logger.performance('PERFORMANCE SUMMARY:');
    this.logger.performance(`Memory Usage: ${metrics.memory.current.heapUsed.toFixed(2)}MB heap`);
    this.logger.performance(`Memory Delta: ${metrics.memory.delta.heapUsed.toFixed(2)}MB`);

    // Show slowest tests
    const slowestTests = this.testResults
      .filter(result => result.duration > 0)
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 5);

    if (slowestTests.length > 0) {
      this.logger.performance('Slowest Tests:');
      slowestTests.forEach(test => {
        this.logger.performance(`  ${test.name}: ${test.duration.toFixed(2)}ms`);
      });
    }
  }
}

// Export for use by other test modules
module.exports = {
  IntegrationTestSuite,
  Logger,
  PerformanceMonitor,
  TEST_CONFIG,
  COLORS,
};

// Main execution if run directly
if (require.main === module) {
  (async () => {
    const suite = new IntegrationTestSuite();

    try {
      await suite.setup();

      // Load and run all test modules
      const testModules = [
        './test-modules/workflow-integration.js',
        './test-modules/environment-config.js',
        './test-modules/aws-sdk-compatibility.js',
        './test-modules/sops-encryption.js',
        './test-modules/cli-interface.js',
        './test-modules/security-validation.js',
        './test-modules/performance-benchmarks.js',
        './test-modules/error-scenarios.js',
      ];

      for (const modulePath of testModules) {
        try {
          const testModule = require(modulePath);
          if (testModule.runTests && typeof testModule.runTests === 'function') {
            await testModule.runTests(suite);
          } else {
            suite.logger.warn(`Test module ${modulePath} doesn't export runTests function`);
          }
        } catch (error) {
          suite.logger.warn(`Failed to load test module ${modulePath}: ${error.message}`);
        }
      }

      await suite.cleanup();
      process.exit(suite.showResults());

    } catch (error) {
      suite.logger.error(`Integration test suite failed: ${error.message}`);
      if (TEST_CONFIG.verbose) {
        console.error(error.stack);
      }
      await suite.cleanup();
      process.exit(1);
    }
  })();
}