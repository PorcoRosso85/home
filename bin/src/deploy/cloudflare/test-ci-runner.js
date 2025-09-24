#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * CI-Ready Integration Test Runner
 *
 * A comprehensive test runner designed for continuous integration environments.
 * Provides proper exit codes, structured output, test reporting, and handles
 * CI-specific requirements like timeouts, parallel execution, and artifact generation.
 *
 * Features:
 * - CI-friendly output formats (TAP, JUnit, JSON)
 * - Proper exit codes for CI systems
 * - Test categorization and filtering
 * - Parallel test execution
 * - Timeout handling
 * - Test artifact generation
 * - Integration with existing CI tools
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Import the comprehensive test suite
const { IntegrationTestSuite, TEST_CONFIG, COLORS } = require('./test-integration-comprehensive.js');

/**
 * CI Configuration
 */
const CI_CONFIG = {
  // Output formats
  outputFormat: process.env.TEST_OUTPUT_FORMAT || 'console', // console, tap, junit, json
  outputFile: process.env.TEST_OUTPUT_FILE || null,

  // Test filtering
  category: process.env.TEST_CATEGORY || null, // E2E_WORKFLOW, ENV_CONFIG, AWS_SDK_COMPAT, etc.
  skipSlow: process.env.SKIP_SLOW_TESTS === 'true',
  skipSops: process.env.SKIP_SOPS_TESTS === 'true',

  // CI environment detection
  isCI: process.env.CI === 'true' || process.env.GITHUB_ACTIONS === 'true' || process.env.JENKINS_URL,

  // Timeouts
  globalTimeout: parseInt(process.env.TEST_TIMEOUT || '1800000'), // 30 minutes default
  testTimeout: parseInt(process.env.INDIVIDUAL_TEST_TIMEOUT || '120000'), // 2 minutes per test

  // Parallel execution
  parallel: process.env.TEST_PARALLEL === 'true',
  maxParallel: parseInt(process.env.MAX_PARALLEL_TESTS || '4'),

  // Artifacts
  generateArtifacts: process.env.GENERATE_TEST_ARTIFACTS === 'true' || process.env.CI === 'true',
  artifactsDir: process.env.TEST_ARTIFACTS_DIR || './test-artifacts',

  // Retry configuration
  retryFailed: process.env.RETRY_FAILED_TESTS === 'true',
  maxRetries: parseInt(process.env.MAX_TEST_RETRIES || '2'),
};

/**
 * CI-Ready Test Runner
 */
class CITestRunner {
  constructor() {
    this.suite = new IntegrationTestSuite();
    this.startTime = Date.now();
    this.results = [];
    this.artifacts = [];
    this.retryQueue = [];
  }

  /**
   * Main entry point for CI test execution
   */
  async run() {
    try {
      this.logCI('info', 'Starting CI Integration Test Suite');
      this.logCI('info', `Configuration: ${JSON.stringify(CI_CONFIG, null, 2)}`);

      // Setup
      await this.setupCIEnvironment();
      await this.suite.setup();

      // Run tests
      const testCategories = this.getTestCategories();

      if (CI_CONFIG.parallel && testCategories.length > 1) {
        await this.runTestsParallel(testCategories);
      } else {
        await this.runTestsSequential(testCategories);
      }

      // Handle retries
      if (CI_CONFIG.retryFailed && this.retryQueue.length > 0) {
        await this.runRetries();
      }

      // Generate outputs and artifacts
      await this.generateTestOutputs();
      await this.generateArtifacts();

      // Cleanup
      await this.suite.cleanup();

      // Final results
      return this.generateFinalResults();

    } catch (error) {
      this.logCI('error', `Test suite failed: ${error.message}`);
      if (CI_CONFIG.outputFormat === 'console') {
        console.error(error.stack);
      }

      await this.generateErrorArtifacts(error);
      return this.exitWithError(error);
    }
  }

  /**
   * Setup CI environment
   */
  async setupCIEnvironment() {
    this.logCI('info', 'Setting up CI environment...');

    // Create artifacts directory
    if (CI_CONFIG.generateArtifacts) {
      if (!fs.existsSync(CI_CONFIG.artifactsDir)) {
        fs.mkdirSync(CI_CONFIG.artifactsDir, { recursive: true });
      }
    }

    // Set CI-specific test configuration
    TEST_CONFIG.skipSops = CI_CONFIG.skipSops;
    TEST_CONFIG.skipCI = false;
    TEST_CONFIG.timeout = CI_CONFIG.testTimeout;
    TEST_CONFIG.verbose = CI_CONFIG.isCI ? false : TEST_CONFIG.verbose;

    // Environment validation
    await this.validateCIEnvironment();

    this.logCI('info', 'CI environment setup complete');
  }

  /**
   * Validate CI environment requirements
   */
  async validateCIEnvironment() {
    const requirements = [
      { name: 'Node.js', check: () => process.version },
      { name: 'npm/node_modules', check: () => fs.existsSync('node_modules') || fs.existsSync('package.json') },
      { name: 'Git repository', check: () => fs.existsSync('.git') },
      { name: 'Test modules', check: () => fs.existsSync('test-modules') },
    ];

    for (const req of requirements) {
      try {
        const result = req.check();
        if (result) {
          this.logCI('debug', `✓ ${req.name}: ${result === true ? 'OK' : result}`);
        } else {
          this.logCI('warn', `✗ ${req.name}: Missing`);
        }
      } catch (error) {
        this.logCI('warn', `✗ ${req.name}: ${error.message}`);
      }
    }

    // Check optional dependencies
    const optionalDeps = [
      { name: 'just', command: 'just --version' },
      { name: 'nix', command: 'nix --version' },
      { name: 'sops', command: 'sops --version' },
    ];

    for (const dep of optionalDeps) {
      try {
        execSync(dep.command, { stdio: 'ignore' });
        this.logCI('debug', `✓ ${dep.name}: Available`);
      } catch (error) {
        this.logCI('debug', `- ${dep.name}: Not available`);
      }
    }
  }

  /**
   * Get test categories to run
   */
  getTestCategories() {
    const allCategories = [
      'E2E_WORKFLOW',
      'ENV_CONFIG',
      'AWS_SDK_COMPAT',
      'SOPS_ENCRYPTION',
      'CLI_INTERFACE',
      'SECURITY',
      'PERFORMANCE',
      'ERROR_SCENARIOS'
    ];

    if (CI_CONFIG.category) {
      const requested = CI_CONFIG.category.split(',').map(c => c.trim());
      return allCategories.filter(cat => requested.includes(cat));
    }

    // Filter out slow tests if requested
    if (CI_CONFIG.skipSlow) {
      return allCategories.filter(cat => !['PERFORMANCE', 'ERROR_SCENARIOS'].includes(cat));
    }

    return allCategories;
  }

  /**
   * Run tests sequentially
   */
  async runTestsSequential(categories) {
    this.logCI('info', `Running tests sequentially: ${categories.join(', ')}`);

    for (const category of categories) {
      await this.runTestCategory(category);
    }
  }

  /**
   * Run tests in parallel
   */
  async runTestsParallel(categories) {
    this.logCI('info', `Running tests in parallel: ${categories.join(', ')}`);

    const chunks = this.chunkArray(categories, CI_CONFIG.maxParallel);

    for (const chunk of chunks) {
      const promises = chunk.map(category => this.runTestCategory(category));
      await Promise.allSettled(promises);
    }
  }

  /**
   * Run a specific test category
   */
  async runTestCategory(category) {
    this.logCI('info', `Starting category: ${category}`);

    const categoryStartTime = Date.now();

    try {
      // Load and run the test module
      const moduleMap = {
        'E2E_WORKFLOW': './test-modules/workflow-integration.js',
        'ENV_CONFIG': './test-modules/environment-config.js',
        'AWS_SDK_COMPAT': './test-modules/aws-sdk-compatibility.js',
        'SOPS_ENCRYPTION': './test-modules/sops-encryption.js',
        'CLI_INTERFACE': './test-modules/cli-interface.js',
        'SECURITY': './test-modules/security-validation.js',
        'PERFORMANCE': './test-modules/performance-benchmarks.js',
        'ERROR_SCENARIOS': './test-modules/error-scenarios.js'
      };

      const modulePath = moduleMap[category];
      if (!modulePath) {
        throw new Error(`Unknown test category: ${category}`);
      }

      const testModule = require(modulePath);
      await testModule.runTests(this.suite);

      const categoryDuration = Date.now() - categoryStartTime;
      this.logCI('info', `Completed category: ${category} (${categoryDuration}ms)`);

    } catch (error) {
      const categoryDuration = Date.now() - categoryStartTime;
      this.logCI('error', `Failed category: ${category} (${categoryDuration}ms) - ${error.message}`);

      // Add to retry queue if retries are enabled
      if (CI_CONFIG.retryFailed) {
        this.retryQueue.push({ category, error, attempt: 1 });
      }
    }
  }

  /**
   * Run test retries
   */
  async runRetries() {
    if (this.retryQueue.length === 0) return;

    this.logCI('info', `Running retries for ${this.retryQueue.length} failed categories`);

    const retryResults = [];

    for (const retry of this.retryQueue) {
      if (retry.attempt > CI_CONFIG.maxRetries) continue;

      this.logCI('info', `Retry ${retry.attempt}/${CI_CONFIG.maxRetries}: ${retry.category}`);

      try {
        await this.runTestCategory(retry.category);
        retryResults.push({ ...retry, success: true });
        this.logCI('info', `Retry successful: ${retry.category}`);

      } catch (error) {
        retryResults.push({ ...retry, success: false, lastError: error });
        this.logCI('warn', `Retry failed: ${retry.category} - ${error.message}`);

        // Add back to queue for next retry
        if (retry.attempt < CI_CONFIG.maxRetries) {
          this.retryQueue.push({ ...retry, attempt: retry.attempt + 1 });
        }
      }
    }

    // Clear processed retries
    this.retryQueue = this.retryQueue.filter(retry => retry.attempt <= CI_CONFIG.maxRetries);
  }

  /**
   * Generate test outputs in various formats
   */
  async generateTestOutputs() {
    const results = this.suite.showResults();

    switch (CI_CONFIG.outputFormat) {
      case 'tap':
        await this.generateTAPOutput();
        break;
      case 'junit':
        await this.generateJUnitOutput();
        break;
      case 'json':
        await this.generateJSONOutput();
        break;
      default:
        // Console output already handled by suite
        break;
    }

    return results;
  }

  /**
   * Generate TAP (Test Anything Protocol) output
   */
  async generateTAPOutput() {
    const results = this.suite.testResults;
    let tapOutput = `TAP version 13\n1..${results.length}\n`;

    results.forEach((result, index) => {
      const testNumber = index + 1;
      const status = result.status === 'completed' ? 'ok' : 'not ok';
      const description = result.name.replace(/[#\n]/g, ' ');

      tapOutput += `${status} ${testNumber} - ${description}\n`;

      if (result.status === 'failed' && result.error) {
        tapOutput += `  ---\n`;
        tapOutput += `  message: "${result.error.message.replace(/"/g, '\\"')}"\n`;
        tapOutput += `  severity: fail\n`;
        tapOutput += `  data:\n`;
        tapOutput += `    duration: ${result.duration}\n`;
        tapOutput += `    category: ${result.category}\n`;
        tapOutput += `  ...\n`;
      }
    });

    await this.writeOutput('tap', tapOutput);
  }

  /**
   * Generate JUnit XML output
   */
  async generateJUnitOutput() {
    const results = this.suite.testResults;
    const totalDuration = (Date.now() - this.startTime) / 1000;

    let junitXML = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    junitXML += `<testsuite name="R2ConnectionIntegrationTests" `;
    junitXML += `tests="${results.length}" `;
    junitXML += `failures="${this.suite.failed}" `;
    junitXML += `errors="0" `;
    junitXML += `skipped="${this.suite.skipped}" `;
    junitXML += `time="${totalDuration}">\n`;

    results.forEach(result => {
      const duration = (result.duration || 0) / 1000;
      const className = result.category || 'Integration';
      const testName = result.name.replace(/[<>&"']/g, '');

      junitXML += `  <testcase classname="${className}" name="${testName}" time="${duration}">`;

      if (result.status === 'failed' && result.error) {
        junitXML += `\n    <failure message="${result.error.message.replace(/[<>&"']/g, '')}">\n`;
        junitXML += `      <![CDATA[${result.error.stack || result.error.message}]]>\n`;
        junitXML += `    </failure>\n  `;
      } else if (result.status === 'skipped') {
        junitXML += `\n    <skipped/>\n  `;
      }

      junitXML += `</testcase>\n`;
    });

    junitXML += `</testsuite>\n`;

    await this.writeOutput('junit.xml', junitXML);
  }

  /**
   * Generate JSON output
   */
  async generateJSONOutput() {
    const jsonReport = {
      summary: {
        total: this.suite.passed + this.suite.failed + this.suite.skipped,
        passed: this.suite.passed,
        failed: this.suite.failed,
        skipped: this.suite.skipped,
        duration: Date.now() - this.startTime,
        timestamp: new Date().toISOString(),
        environment: {
          ci: CI_CONFIG.isCI,
          node: process.version,
          platform: process.platform,
          arch: process.arch
        }
      },
      tests: this.suite.testResults.map(result => ({
        name: result.name,
        category: result.category,
        status: result.status,
        duration: result.duration,
        error: result.error ? {
          message: result.error.message,
          stack: result.error.stack
        } : null,
        performance: result.performance
      })),
      config: CI_CONFIG,
      artifacts: this.artifacts
    };

    await this.writeOutput('json', JSON.stringify(jsonReport, null, 2));
  }

  /**
   * Generate test artifacts
   */
  async generateArtifacts() {
    if (!CI_CONFIG.generateArtifacts) return;

    this.logCI('info', 'Generating test artifacts...');

    // Performance report
    if (this.suite.testResults.some(r => r.performance)) {
      await this.generatePerformanceArtifact();
    }

    // Error logs
    const failedTests = this.suite.testResults.filter(r => r.status === 'failed');
    if (failedTests.length > 0) {
      await this.generateErrorArtifact(failedTests);
    }

    // Environment snapshot
    await this.generateEnvironmentArtifact();

    // Coverage report (if available)
    await this.generateCoverageArtifact();

    this.logCI('info', `Generated ${this.artifacts.length} test artifacts`);
  }

  /**
   * Generate performance artifact
   */
  async generatePerformanceArtifact() {
    const performanceData = this.suite.testResults
      .filter(r => r.performance)
      .map(r => ({
        test: r.name,
        category: r.category,
        duration: r.duration,
        memory: r.performance.memory,
        timings: r.performance.timings
      }));

    const performanceReport = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: performanceData.length,
        averageDuration: performanceData.reduce((sum, p) => sum + p.duration, 0) / performanceData.length,
        slowestTest: performanceData.reduce((max, p) => p.duration > max.duration ? p : max, { duration: 0 })
      },
      tests: performanceData
    };

    const filePath = path.join(CI_CONFIG.artifactsDir, 'performance-report.json');
    fs.writeFileSync(filePath, JSON.stringify(performanceReport, null, 2));
    this.artifacts.push(filePath);
  }

  /**
   * Generate error artifact
   */
  async generateErrorArtifact(failedTests) {
    const errorReport = {
      timestamp: new Date().toISOString(),
      failedCount: failedTests.length,
      errors: failedTests.map(test => ({
        name: test.name,
        category: test.category,
        error: test.error.message,
        stack: test.error.stack,
        duration: test.duration
      }))
    };

    const filePath = path.join(CI_CONFIG.artifactsDir, 'error-report.json');
    fs.writeFileSync(filePath, JSON.stringify(errorReport, null, 2));
    this.artifacts.push(filePath);
  }

  /**
   * Generate environment artifact
   */
  async generateEnvironmentArtifact() {
    const environmentInfo = {
      timestamp: new Date().toISOString(),
      system: {
        platform: process.platform,
        arch: process.arch,
        node: process.version,
        memory: process.memoryUsage(),
        uptime: process.uptime()
      },
      environment: Object.keys(process.env)
        .filter(key => key.startsWith('TEST_') || key.startsWith('CI') || key.startsWith('GITHUB_'))
        .reduce((env, key) => {
          env[key] = process.env[key];
          return env;
        }, {}),
      dependencies: this.getInstalledPackages(),
      testConfig: TEST_CONFIG,
      ciConfig: CI_CONFIG
    };

    const filePath = path.join(CI_CONFIG.artifactsDir, 'environment-snapshot.json');
    fs.writeFileSync(filePath, JSON.stringify(environmentInfo, null, 2));
    this.artifacts.push(filePath);
  }

  /**
   * Generate coverage artifact (if available)
   */
  async generateCoverageArtifact() {
    // Check if coverage data is available
    const coveragePaths = [
      'coverage/coverage-final.json',
      'coverage/lcov.info',
      '.nyc_output/coverage.json'
    ];

    for (const coveragePath of coveragePaths) {
      if (fs.existsSync(coveragePath)) {
        const targetPath = path.join(CI_CONFIG.artifactsDir, path.basename(coveragePath));
        fs.copyFileSync(coveragePath, targetPath);
        this.artifacts.push(targetPath);
      }
    }
  }

  /**
   * Generate error artifacts on failure
   */
  async generateErrorArtifacts(error) {
    if (!CI_CONFIG.generateArtifacts) return;

    const errorArtifact = {
      timestamp: new Date().toISOString(),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name
      },
      environment: {
        node: process.version,
        platform: process.platform,
        memory: process.memoryUsage(),
        cwd: process.cwd()
      },
      config: CI_CONFIG
    };

    try {
      const filePath = path.join(CI_CONFIG.artifactsDir, 'fatal-error.json');
      fs.writeFileSync(filePath, JSON.stringify(errorArtifact, null, 2));
    } catch (writeError) {
      console.error('Failed to write error artifact:', writeError.message);
    }
  }

  /**
   * Generate final results and exit code
   */
  generateFinalResults() {
    const totalTests = this.suite.passed + this.suite.failed + this.suite.skipped;
    const duration = Date.now() - this.startTime;

    const results = {
      success: this.suite.failed === 0,
      summary: {
        total: totalTests,
        passed: this.suite.passed,
        failed: this.suite.failed,
        skipped: this.suite.skipped,
        duration: duration
      },
      exitCode: this.suite.failed === 0 ? 0 : 1,
      artifacts: this.artifacts
    };

    this.logCI('info', `Test Results: ${results.summary.passed}/${results.summary.total} passed, ${results.summary.failed} failed, ${results.summary.skipped} skipped`);
    this.logCI('info', `Total Duration: ${(duration / 1000).toFixed(2)}s`);

    if (results.artifacts.length > 0) {
      this.logCI('info', `Artifacts: ${results.artifacts.join(', ')}`);
    }

    return results;
  }

  /**
   * Exit with error
   */
  exitWithError(error) {
    return {
      success: false,
      error: error.message,
      exitCode: 1,
      artifacts: this.artifacts
    };
  }

  /**
   * Write output to file or console
   */
  async writeOutput(extension, content) {
    if (CI_CONFIG.outputFile) {
      const filePath = CI_CONFIG.outputFile.replace(/\.[^.]+$/, `.${extension}`);
      fs.writeFileSync(filePath, content);
      this.logCI('info', `Output written to: ${filePath}`);
    } else if (CI_CONFIG.outputFormat !== 'console') {
      console.log(content);
    }
  }

  /**
   * CI-appropriate logging
   */
  logCI(level, message) {
    const timestamp = new Date().toISOString();

    if (CI_CONFIG.isCI) {
      // Structured logging for CI
      console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
    } else {
      // Colored logging for local development
      const colors = {
        info: COLORS.cyan,
        warn: COLORS.yellow,
        error: COLORS.red,
        debug: COLORS.blue
      };

      const color = colors[level] || COLORS.reset;
      console.log(`${color}[${level.toUpperCase()}]${COLORS.reset} ${message}`);
    }
  }

  /**
   * Utility: Chunk array into smaller arrays
   */
  chunkArray(array, chunkSize) {
    const chunks = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  }

  /**
   * Get installed packages
   */
  getInstalledPackages() {
    try {
      const packageJsonPath = path.join(process.cwd(), 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        return {
          name: packageJson.name,
          version: packageJson.version,
          dependencies: packageJson.dependencies,
          devDependencies: packageJson.devDependencies
        };
      }
    } catch (error) {
      // Ignore package.json parsing errors
    }
    return null;
  }
}

/**
 * Main execution
 */
async function main() {
  // Handle CLI arguments
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log(`
CI-Ready Integration Test Runner

Usage: node test-ci-runner.js [OPTIONS]

Environment Variables:
  TEST_OUTPUT_FORMAT     Output format: console, tap, junit, json (default: console)
  TEST_OUTPUT_FILE       Output file path (optional)
  TEST_CATEGORY          Test categories to run (comma-separated)
  SKIP_SLOW_TESTS        Skip slow test categories (default: false)
  SKIP_SOPS_TESTS        Skip SOPS-related tests (default: false)
  TEST_TIMEOUT           Global timeout in milliseconds (default: 1800000)
  INDIVIDUAL_TEST_TIMEOUT Test timeout in milliseconds (default: 120000)
  TEST_PARALLEL          Run tests in parallel (default: false)
  MAX_PARALLEL_TESTS     Maximum parallel test categories (default: 4)
  GENERATE_TEST_ARTIFACTS Generate test artifacts (default: true in CI)
  TEST_ARTIFACTS_DIR     Artifacts directory (default: ./test-artifacts)
  RETRY_FAILED_TESTS     Retry failed tests (default: false)
  MAX_TEST_RETRIES       Maximum retry attempts (default: 2)

Examples:
  # Run all tests
  node test-ci-runner.js

  # Run specific categories
  TEST_CATEGORY=E2E_WORKFLOW,SECURITY node test-ci-runner.js

  # Generate JUnit output
  TEST_OUTPUT_FORMAT=junit TEST_OUTPUT_FILE=test-results.xml node test-ci-runner.js

  # CI mode with parallel execution
  CI=true TEST_PARALLEL=true GENERATE_TEST_ARTIFACTS=true node test-ci-runner.js
    `);
    process.exit(0);
  }

  // Global timeout handler
  const globalTimeoutHandle = setTimeout(() => {
    console.error(`❌ Global timeout reached (${CI_CONFIG.globalTimeout}ms)`);
    process.exit(124); // Timeout exit code
  }, CI_CONFIG.globalTimeout);

  try {
    const runner = new CITestRunner();
    const results = await runner.run();

    clearTimeout(globalTimeoutHandle);

    // Exit with appropriate code
    process.exit(results.exitCode);

  } catch (error) {
    clearTimeout(globalTimeoutHandle);

    console.error('❌ Test runner failed:', error.message);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }

    process.exit(1);
  }
}

// Export for testing
module.exports = {
  CITestRunner,
  CI_CONFIG
};

// Run if called directly
if (require.main === module) {
  main();
}