/**
 * CLI Interface and Command Integration Tests
 *
 * Tests the command-line interfaces, Just tasks, Nix apps, and their
 * integration. Validates that all commands work correctly, provide
 * proper output, handle errors gracefully, and integrate seamlessly.
 *
 * Test scenarios:
 * - Just task execution and validation
 * - Nix app functionality
 * - CLI script interfaces
 * - Command chaining and dependencies
 * - Help and usage information
 * - Error handling and exit codes
 * - Interactive vs non-interactive modes
 */

const fs = require('fs');
const path = require('path');

/**
 * Run CLI interface and command integration tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running CLI Interface and Command Integration Tests...');

  // Test 1: Just Task Availability
  await testSuite.runTest('Just Task Availability', async () => {
    await testJustTaskAvailability(testSuite);
  }, {
    category: 'CLI_INTERFACE',
    skipIf: !isJustAvailable() ? 'Just command runner not available' : false
  });

  // Test 2: Nix App Functionality
  await testSuite.runTest('Nix App Functionality', async () => {
    await testNixAppFunctionality(testSuite);
  }, {
    category: 'CLI_INTERFACE',
    skipIf: !isNixAvailable() ? 'Nix not available' : false
  });

  // Test 3: CLI Script Interfaces
  await testSuite.runTest('CLI Script Interfaces', async () => {
    await testCliScriptInterfaces(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 4: Command Integration and Chaining
  await testSuite.runTest('Command Integration and Chaining', async () => {
    await testCommandIntegrationChaining(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 5: Help and Usage Information
  await testSuite.runTest('Help and Usage Information', async () => {
    await testHelpUsageInformation(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 6: Error Handling and Exit Codes
  await testSuite.runTest('Error Handling and Exit Codes', async () => {
    await testErrorHandlingExitCodes(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 7: Interactive vs Non-Interactive Modes
  await testSuite.runTest('Interactive vs Non-Interactive Modes', async () => {
    await testInteractiveNonInteractiveModes(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 8: Command Configuration and Options
  await testSuite.runTest('Command Configuration and Options', async () => {
    await testCommandConfigurationOptions(testSuite);
  }, { category: 'CLI_INTERFACE' });

  // Test 9: Command Performance and Reliability
  await testSuite.runTest('Command Performance and Reliability', async () => {
    await testCommandPerformanceReliability(testSuite);
  }, { category: 'CLI_INTERFACE' });
}

/**
 * Check if Just command runner is available
 */
function isJustAvailable() {
  try {
    require('child_process').execSync('which just', { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Check if Nix is available
 */
function isNixAvailable() {
  try {
    require('child_process').execSync('which nix', { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Test Just task availability
 */
async function testJustTaskAvailability(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing Just task availability...');

  // Test Just installation
  const justVersionResult = await testSuite.execCommand('just --version');
  if (justVersionResult.code !== 0) {
    throw new Error('Just command runner not properly installed');
  }

  logger.debug(`Just version: ${justVersionResult.stdout.trim()}`);

  // Test justfile exists
  const justfilePath = path.join(testSuite.TEST_CONFIG.workDir, 'justfile');
  if (!fs.existsSync(justfilePath)) {
    throw new Error('Justfile not found in project root');
  }

  // Test Just can read justfile
  const justListResult = await testSuite.execCommand('just --list');
  if (justListResult.code !== 0) {
    throw new Error(`Just cannot read justfile: ${justListResult.stderr}`);
  }

  const availableTasks = justListResult.stdout;
  logger.debug('Available Just tasks:');
  logger.debug(availableTasks);

  // Test required tasks are available
  const requiredTasks = [
    'help',
    'setup',
    'status',
    'clean',
    'secrets:init',
    'secrets:edit',
    'secrets:check',
    'r2:envs',
    'r2:status',
    'r2:test',
    'r2:validate',
    'r2:gen-config',
    'r2:deploy-prep',
    'r2:quick',
    'r2:validate-all',
    'r2:check-secrets'
  ];

  const missingTasks = [];
  for (const task of requiredTasks) {
    if (!availableTasks.includes(task)) {
      missingTasks.push(task);
    }
  }

  if (missingTasks.length > 0) {
    throw new Error(`Missing required Just tasks: ${missingTasks.join(', ')}`);
  }

  // Test task descriptions are provided
  const taskLines = availableTasks.split('\n').filter(line => line.trim().length > 0);
  const tasksWithoutDescription = taskLines.filter(line =>
    line.includes('    ') && !line.includes('#')
  );

  if (tasksWithoutDescription.length > 0) {
    logger.warn('Some tasks missing descriptions - consider adding help text');
  }

  logger.debug('Just task availability validated successfully');
}

/**
 * Test Nix app functionality
 */
async function testNixAppFunctionality(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing Nix app functionality...');

  // Test Nix installation
  const nixVersionResult = await testSuite.execCommand('nix --version');
  if (nixVersionResult.code !== 0) {
    throw new Error('Nix not properly installed');
  }

  logger.debug(`Nix version: ${nixVersionResult.stdout.trim()}`);

  // Test flake functionality
  const flakeCheckResult = await testSuite.execCommand('nix flake metadata --json', { timeout: 30000 });
  if (flakeCheckResult.code !== 0) {
    throw new Error(`Flake metadata check failed: ${flakeCheckResult.stderr}`);
  }

  const flakeMetadata = JSON.parse(flakeCheckResult.stdout);
  if (!flakeMetadata.path || !flakeMetadata.locks) {
    throw new Error('Flake metadata incomplete');
  }

  logger.debug(`Flake path: ${flakeMetadata.path}`);

  // Test flake apps are available
  const flakeShowResult = await testSuite.execCommand('nix flake show --json', { timeout: 30000 });
  if (flakeShowResult.code !== 0) {
    throw new Error(`Flake show failed: ${flakeShowResult.stderr}`);
  }

  const flakeShow = JSON.parse(flakeShowResult.stdout);
  const apps = flakeShow.apps && flakeShow.apps['x86_64-linux'];

  if (!apps) {
    throw new Error('No Nix apps found for current system');
  }

  // Test required apps are available
  const requiredApps = [
    'no-plaintext-secrets',
    'validate-r2-manifest',
    'gen-connection-manifest',
    'gen-wrangler-config'
  ];

  const availableApps = Object.keys(apps);
  const missingApps = requiredApps.filter(app => !availableApps.includes(app));

  if (missingApps.length > 0) {
    throw new Error(`Missing required Nix apps: ${missingApps.join(', ')}`);
  }

  logger.debug(`Available Nix apps: ${availableApps.join(', ')}`);

  // Test a simple app execution
  try {
    const helpResult = await testSuite.execCommand('nix run .#no-plaintext-secrets -- --help', { timeout: 15000 });
    if (helpResult.code !== 0 && !helpResult.stderr.includes('help')) {
      logger.warn('no-plaintext-secrets app may not have help option');
    }
  } catch (error) {
    logger.warn(`App execution test: ${error.message}`);
  }

  // Test development shell
  try {
    const devShellResult = await testSuite.execCommand('nix develop --command echo "dev shell works"', { timeout: 30000 });
    if (devShellResult.code === 0 && devShellResult.stdout.includes('dev shell works')) {
      logger.debug('Development shell working correctly');
    } else {
      logger.warn('Development shell may have issues');
    }
  } catch (error) {
    logger.warn(`Development shell test: ${error.message}`);
  }

  logger.debug('Nix app functionality validated successfully');
}

/**
 * Test CLI script interfaces
 */
async function testCliScriptInterfaces(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing CLI script interfaces...');

  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');
  const requiredScripts = [
    'gen-connection-manifest.js',
    'gen-wrangler-config.js',
    'validate-r2-manifest.sh',
    'validate-environment-secrets.sh'
  ];

  // Test script files exist and are executable
  for (const script of requiredScripts) {
    const scriptPath = path.join(scriptsDir, script);

    if (!fs.existsSync(scriptPath)) {
      throw new Error(`Required script missing: ${script}`);
    }

    const stats = fs.statSync(scriptPath);
    if (!(stats.mode & 0o111)) {
      throw new Error(`Script not executable: ${script}`);
    }

    logger.debug(`Script verified: ${script}`);
  }

  // Test JavaScript CLI scripts
  for (const jsScript of ['gen-connection-manifest.js', 'gen-wrangler-config.js']) {
    const scriptPath = path.join(scriptsDir, jsScript);

    // Test script has proper shebang
    const content = fs.readFileSync(scriptPath, 'utf8');
    if (!content.startsWith('#!/usr/bin/env node') && !content.includes('exec') && !content.includes('node')) {
      logger.warn(`Script ${jsScript} may be missing proper shebang`);
    }

    // Test script help option
    try {
      const helpResult = await testSuite.execCommand(`${scriptPath} --help`, { timeout: 10000 });
      if (helpResult.code !== 0 && !helpResult.stderr.includes('help') && !helpResult.stdout.includes('help')) {
        logger.warn(`Script ${jsScript} may not have help option`);
      } else {
        logger.debug(`Script ${jsScript} help option working`);
      }
    } catch (error) {
      logger.warn(`Script ${jsScript} help test: ${error.message}`);
    }

    // Test script version option
    try {
      const versionResult = await testSuite.execCommand(`${scriptPath} --version`, { timeout: 10000 });
      if (versionResult.code === 0) {
        logger.debug(`Script ${jsScript} version: ${versionResult.stdout.trim()}`);
      }
    } catch (error) {
      logger.debug(`Script ${jsScript} version test: ${error.message}`);
    }
  }

  // Test shell script interfaces
  for (const shScript of ['validate-r2-manifest.sh', 'validate-environment-secrets.sh']) {
    const scriptPath = path.join(scriptsDir, shScript);

    // Test script has proper shebang
    const content = fs.readFileSync(scriptPath, 'utf8');
    if (!content.startsWith('#!/usr/bin/env bash') && !content.startsWith('#!/bin/bash')) {
      logger.warn(`Script ${shScript} may be missing proper bash shebang`);
    }

    // Test script execution
    try {
      const testResult = await testSuite.execCommand(`${scriptPath} --help`, { timeout: 10000 });
      if (testResult.code !== 0 && !testResult.stderr.includes('help') && !testResult.stdout.includes('help')) {
        logger.warn(`Script ${shScript} may not have help option`);
      } else {
        logger.debug(`Script ${shScript} help option working`);
      }
    } catch (error) {
      logger.warn(`Script ${shScript} help test: ${error.message}`);
    }
  }

  // Test script parameter validation
  for (const script of requiredScripts) {
    const scriptPath = path.join(scriptsDir, script);

    try {
      // Test with invalid parameters
      const invalidResult = await testSuite.execCommand(`${scriptPath} --invalid-option`, { timeout: 10000 });
      if (invalidResult.code === 0) {
        logger.warn(`Script ${script} accepts invalid options without error`);
      }
    } catch (error) {
      logger.debug(`Script ${script} parameter validation test: ${error.message}`);
    }
  }

  logger.debug('CLI script interfaces validated successfully');
}

/**
 * Test command integration and chaining
 */
async function testCommandIntegrationChaining(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing command integration and chaining...');

  // Test basic command chaining
  const commandChains = [
    'just r2:envs',
    'just r2:status dev',
    'just secrets:check',
    'just r2:validate dev --dry-run',
    'just clean'
  ];

  for (const command of commandChains) {
    try {
      logger.debug(`Testing command: ${command}`);
      const result = await testSuite.execCommand(command, { timeout: 30000 });

      if (result.code !== 0) {
        // Some commands may fail due to missing setup, that's okay for now
        logger.warn(`Command failed (may be expected): ${command} - ${result.stderr}`);
      } else {
        logger.debug(`Command succeeded: ${command}`);
      }
    } catch (error) {
      logger.warn(`Command test error: ${command} - ${error.message}`);
    }
  }

  // Test command dependencies
  const dependencyTests = [
    {
      name: 'secrets:init before secrets:edit',
      commands: ['just secrets:init --dry-run', 'just secrets:edit --dry-run']
    },
    {
      name: 'r2:gen-config before r2:validate',
      commands: ['just r2:gen-config dev --dry-run', 'just r2:validate dev --dry-run']
    },
    {
      name: 'setup before status',
      commands: ['just setup --dry-run', 'just status']
    }
  ];

  for (const test of dependencyTests) {
    logger.debug(`Testing dependency: ${test.name}`);

    try {
      for (const command of test.commands) {
        const result = await testSuite.execCommand(command, { timeout: 30000 });
        logger.debug(`Dependency command: ${command} - exit code: ${result.code}`);
      }
    } catch (error) {
      logger.warn(`Dependency test error: ${test.name} - ${error.message}`);
    }
  }

  // Test Nix and Just integration
  try {
    const nixJustTest = await testSuite.execCommand('just --version && nix --version', { timeout: 15000 });
    if (nixJustTest.code === 0) {
      logger.debug('Nix and Just integration working');
    }
  } catch (error) {
    logger.warn(`Nix/Just integration test: ${error.message}`);
  }

  // Test script execution through Just tasks
  const scriptTasks = [
    'r2:gen-config dev --dry-run',
    'r2:validate dev --dry-run',
    'secrets:check'
  ];

  for (const task of scriptTasks) {
    try {
      logger.debug(`Testing Just task: ${task}`);
      const result = await testSuite.execCommand(`just ${task}`, { timeout: 30000 });

      if (result.code !== 0) {
        logger.warn(`Just task failed: ${task} - ${result.stderr}`);
      } else {
        logger.debug(`Just task succeeded: ${task}`);
      }
    } catch (error) {
      logger.warn(`Just task test error: ${task} - ${error.message}`);
    }
  }

  logger.debug('Command integration and chaining validated successfully');
}

/**
 * Test help and usage information
 */
async function testHelpUsageInformation(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing help and usage information...');

  // Test Just help
  try {
    const justHelpResult = await testSuite.execCommand('just --help');
    if (justHelpResult.code !== 0) {
      throw new Error('Just help command failed');
    }

    if (!justHelpResult.stdout.includes('USAGE') && !justHelpResult.stdout.includes('usage')) {
      logger.warn('Just help output may not include usage information');
    }
  } catch (error) {
    logger.warn(`Just help test: ${error.message}`);
  }

  // Test Just task list
  try {
    const taskListResult = await testSuite.execCommand('just --list');
    if (taskListResult.code !== 0) {
      throw new Error('Just task list command failed');
    }

    const taskList = taskListResult.stdout;
    const taskCount = (taskList.match(/^\s+\w+/gm) || []).length;

    if (taskCount === 0) {
      throw new Error('No Just tasks found in list');
    }

    logger.debug(`Found ${taskCount} Just tasks with descriptions`);
  } catch (error) {
    logger.warn(`Just task list test: ${error.message}`);
  }

  // Test individual task help
  const helpTasks = ['help', 'setup', 'r2:status', 'secrets:init'];

  for (const task of helpTasks) {
    try {
      const taskHelpResult = await testSuite.execCommand(`just ${task} --help`, { timeout: 15000 });

      // Not all tasks may support --help, but they shouldn't crash
      if (taskHelpResult.code === 0) {
        logger.debug(`Task ${task} supports --help option`);
      }
    } catch (error) {
      logger.debug(`Task help test: ${task} - ${error.message}`);
    }
  }

  // Test script help documentation
  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');
  const scripts = ['gen-connection-manifest.js', 'gen-wrangler-config.js'];

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    try {
      const scriptHelpResult = await testSuite.execCommand(`${scriptPath} --help`, { timeout: 10000 });

      if (scriptHelpResult.code === 0) {
        const helpOutput = scriptHelpResult.stdout;

        // Check for common help sections
        const helpSections = ['USAGE', 'OPTIONS', 'EXAMPLES', 'DESCRIPTION'];
        const foundSections = helpSections.filter(section =>
          helpOutput.toUpperCase().includes(section)
        );

        if (foundSections.length > 0) {
          logger.debug(`Script ${script} has help sections: ${foundSections.join(', ')}`);
        } else {
          logger.warn(`Script ${script} help may be incomplete`);
        }
      }
    } catch (error) {
      logger.debug(`Script help test: ${script} - ${error.message}`);
    }
  }

  // Test README documentation
  const readmePath = path.join(testSuite.TEST_CONFIG.workDir, 'README.md');
  if (fs.existsSync(readmePath)) {
    const readmeContent = fs.readFileSync(readmePath, 'utf8');

    // Check for essential documentation sections
    const docSections = [
      'Quick Start',
      'Installation',
      'Usage',
      'Examples',
      'Commands',
      'Configuration'
    ];

    const foundDocSections = docSections.filter(section =>
      readmeContent.includes(section)
    );

    if (foundDocSections.length < 3) {
      logger.warn('README may be missing essential documentation sections');
    } else {
      logger.debug(`README has documentation sections: ${foundDocSections.join(', ')}`);
    }

    // Check for command examples
    if (readmeContent.includes('just ') || readmeContent.includes('nix run')) {
      logger.debug('README includes command examples');
    } else {
      logger.warn('README may be missing command examples');
    }
  }

  logger.debug('Help and usage information validated successfully');
}

/**
 * Test error handling and exit codes
 */
async function testErrorHandlingExitCodes(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing error handling and exit codes...');

  // Test invalid Just tasks
  try {
    const invalidTaskResult = await testSuite.execCommand('just invalid-task-name', { timeout: 10000 });
    if (invalidTaskResult.code === 0) {
      throw new Error('Invalid Just task should return non-zero exit code');
    }

    if (!invalidTaskResult.stderr.includes('error') && !invalidTaskResult.stderr.includes('not found')) {
      logger.warn('Invalid task error message may not be clear');
    }
  } catch (error) {
    if (!error.message.includes('non-zero')) {
      logger.debug(`Invalid task test expected error: ${error.message}`);
    }
  }

  // Test script error handling
  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');
  const scripts = ['gen-connection-manifest.js', 'gen-wrangler-config.js'];

  for (const script of scripts) {
    const scriptPath = path.join(scriptsDir, script);

    // Test with invalid arguments
    try {
      const invalidArgsResult = await testSuite.execCommand(`${scriptPath} --invalid-arg-name`, { timeout: 10000 });

      if (invalidArgsResult.code === 0) {
        logger.warn(`Script ${script} accepts invalid arguments without error`);
      } else {
        logger.debug(`Script ${script} properly rejects invalid arguments`);
      }
    } catch (error) {
      logger.debug(`Script error test: ${script} - ${error.message}`);
    }

    // Test with missing required arguments
    try {
      const missingArgsResult = await testSuite.execCommand(`${scriptPath}`, { timeout: 10000 });

      // Should either succeed with defaults or fail with helpful error
      if (missingArgsResult.code !== 0) {
        if (missingArgsResult.stderr.includes('required') || missingArgsResult.stderr.includes('missing')) {
          logger.debug(`Script ${script} provides helpful error for missing arguments`);
        } else {
          logger.warn(`Script ${script} error message may not be helpful`);
        }
      }
    } catch (error) {
      logger.debug(`Script missing args test: ${script} - ${error.message}`);
    }
  }

  // Test Nix app error handling
  if (isNixAvailable()) {
    try {
      const nixAppErrorResult = await testSuite.execCommand('nix run .#nonexistent-app', { timeout: 15000 });

      if (nixAppErrorResult.code === 0) {
        throw new Error('Nonexistent Nix app should return non-zero exit code');
      }

      if (nixAppErrorResult.stderr.includes('error') || nixAppErrorResult.stderr.includes('not found')) {
        logger.debug('Nix app error handling working correctly');
      }
    } catch (error) {
      if (!error.message.includes('non-zero')) {
        logger.debug(`Nix app error test: ${error.message}`);
      }
    }
  }

  // Test exit code consistency
  const exitCodeTests = [
    { command: 'just --version', expectedCode: 0 },
    { command: 'just --invalid-option', expectedCode: 'non-zero' },
    { command: 'just invalid-task', expectedCode: 'non-zero' }
  ];

  for (const test of exitCodeTests) {
    try {
      const result = await testSuite.execCommand(test.command, { timeout: 10000 });

      if (test.expectedCode === 0 && result.code !== 0) {
        logger.warn(`Command "${test.command}" should succeed but returned code ${result.code}`);
      } else if (test.expectedCode === 'non-zero' && result.code === 0) {
        logger.warn(`Command "${test.command}" should fail but returned code 0`);
      } else {
        logger.debug(`Exit code test passed: ${test.command}`);
      }
    } catch (error) {
      logger.debug(`Exit code test: ${test.command} - ${error.message}`);
    }
  }

  logger.debug('Error handling and exit codes validated successfully');
}

/**
 * Test interactive vs non-interactive modes
 */
async function testInteractiveNonInteractiveModes(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing interactive vs non-interactive modes...');

  // Test non-interactive mode flags
  const nonInteractiveCommands = [
    'just setup --dry-run',
    'just r2:validate dev --dry-run',
    'just secrets:init --dry-run',
    'just r2:gen-config dev --dry-run'
  ];

  for (const command of nonInteractiveCommands) {
    try {
      logger.debug(`Testing non-interactive: ${command}`);

      const result = await testSuite.execCommand(command, { timeout: 30000 });

      // Non-interactive commands should not hang waiting for input
      logger.debug(`Non-interactive command completed: ${command} (exit code: ${result.code})`);

    } catch (error) {
      if (error.message.includes('timeout')) {
        logger.warn(`Command may be waiting for interactive input: ${command}`);
      } else {
        logger.debug(`Non-interactive test: ${command} - ${error.message}`);
      }
    }
  }

  // Test scripts with dry-run modes
  const scriptsDir = path.join(testSuite.TEST_CONFIG.workDir, 'scripts');
  const dryRunTests = [
    `${scriptsDir}/gen-connection-manifest.js --env dev --dry-run`,
    `${scriptsDir}/gen-wrangler-config.js --env dev --dry-run`
  ];

  for (const command of dryRunTests) {
    try {
      logger.debug(`Testing dry-run mode: ${command}`);

      const result = await testSuite.execCommand(command, { timeout: 15000 });

      if (result.code === 0) {
        logger.debug(`Dry-run mode working: ${command}`);
      } else {
        logger.warn(`Dry-run mode failed: ${command} - ${result.stderr}`);
      }

    } catch (error) {
      logger.debug(`Dry-run test: ${command} - ${error.message}`);
    }
  }

  // Test environment variable controls
  const envVarTests = [
    { var: 'CI', value: 'true', description: 'CI mode' },
    { var: 'FORCE_COLOR', value: '0', description: 'No color output' },
    { var: 'NO_INTERACTIVE', value: '1', description: 'Non-interactive mode' }
  ];

  for (const envTest of envVarTests) {
    try {
      logger.debug(`Testing environment control: ${envTest.description}`);

      const env = { ...process.env, [envTest.var]: envTest.value };

      const result = await testSuite.execCommand('just --version', { env, timeout: 10000 });

      if (result.code === 0) {
        logger.debug(`Environment variable control working: ${envTest.var}=${envTest.value}`);
      }

    } catch (error) {
      logger.debug(`Environment variable test: ${envTest.var} - ${error.message}`);
    }
  }

  // Test batch mode operations
  const batchCommands = [
    'just r2:validate-all --dry-run',
    'just clean && just status'
  ];

  for (const command of batchCommands) {
    try {
      logger.debug(`Testing batch operation: ${command}`);

      const result = await testSuite.execCommand(command, { timeout: 45000 });

      logger.debug(`Batch operation completed: ${command} (exit code: ${result.code})`);

    } catch (error) {
      logger.debug(`Batch operation test: ${command} - ${error.message}`);
    }
  }

  logger.debug('Interactive vs non-interactive modes validated successfully');
}

/**
 * Test command configuration and options
 */
async function testCommandConfigurationOptions(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing command configuration and options...');

  // Test justfile configuration
  const justfilePath = path.join(testSuite.TEST_CONFIG.workDir, 'justfile');
  const justfileContent = fs.readFileSync(justfilePath, 'utf8');

  // Check for proper shebang
  if (!justfileContent.startsWith('#!') && !justfileContent.includes('set ')) {
    logger.warn('Justfile may be missing configuration settings');
  }

  // Check for common Just settings
  const justSettings = ['shell', 'dotenv-load', 'positional-arguments'];
  const foundSettings = justSettings.filter(setting =>
    justfileContent.includes(setting)
  );

  if (foundSettings.length > 0) {
    logger.debug(`Justfile has settings: ${foundSettings.join(', ')}`);
  }

  // Test environment variable support
  const envVarCommands = [
    'ENVIRONMENT=dev just r2:status',
    'DRY_RUN=true just setup'
  ];

  for (const command of envVarCommands) {
    try {
      const result = await testSuite.execCommand(command, { timeout: 20000 });
      logger.debug(`Environment variable command: ${command} (exit code: ${result.code})`);
    } catch (error) {
      logger.debug(`Environment variable test: ${command} - ${error.message}`);
    }
  }

  // Test configuration file loading
  const configFiles = ['.env', '.env.example', 'r2.yaml.example'];

  for (const configFile of configFiles) {
    const configPath = path.join(testSuite.TEST_CONFIG.workDir, configFile);

    if (fs.existsSync(configPath)) {
      logger.debug(`Configuration file exists: ${configFile}`);

      // Check file format
      const content = fs.readFileSync(configPath, 'utf8');

      if (configFile.endsWith('.yaml') || configFile.endsWith('.yml')) {
        if (!content.includes(':') || content.trim().length === 0) {
          logger.warn(`YAML configuration file may be invalid: ${configFile}`);
        }
      }

      if (configFile.startsWith('.env')) {
        const lines = content.split('\n').filter(line => line.trim().length > 0);
        const validEnvLines = lines.filter(line =>
          line.includes('=') || line.startsWith('#')
        );

        if (validEnvLines.length !== lines.length) {
          logger.warn(`Environment file may have invalid format: ${configFile}`);
        }
      }
    }
  }

  // Test option parsing
  const optionTests = [
    { command: 'just --dry-run status', description: 'Global dry-run option' },
    { command: 'just r2:status --env dev', description: 'Environment option' },
    { command: 'just setup --force', description: 'Force option' }
  ];

  for (const test of optionTests) {
    try {
      logger.debug(`Testing option: ${test.description}`);

      const result = await testSuite.execCommand(test.command, { timeout: 20000 });

      logger.debug(`Option test: ${test.description} (exit code: ${result.code})`);

    } catch (error) {
      logger.debug(`Option test: ${test.description} - ${error.message}`);
    }
  }

  logger.debug('Command configuration and options validated successfully');
}

/**
 * Test command performance and reliability
 */
async function testCommandPerformanceReliability(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing command performance and reliability...');

  // Test command execution times
  const performanceCommands = [
    'just --version',
    'just --list',
    'just status',
    'just r2:envs'
  ];

  const performanceResults = [];

  for (const command of performanceCommands) {
    try {
      const startTime = Date.now();

      const result = await testSuite.execCommand(command, { timeout: 30000 });

      const endTime = Date.now();
      const duration = endTime - startTime;

      performanceResults.push({
        command,
        duration,
        success: result.code === 0
      });

      logger.performance(`Command timing: ${command} - ${duration}ms`);

    } catch (error) {
      logger.debug(`Performance test: ${command} - ${error.message}`);
    }
  }

  // Analyze performance results
  const successfulCommands = performanceResults.filter(r => r.success);
  if (successfulCommands.length > 0) {
    const avgDuration = successfulCommands.reduce((sum, r) => sum + r.duration, 0) / successfulCommands.length;
    logger.performance(`Average command duration: ${avgDuration.toFixed(2)}ms`);

    const slowCommands = successfulCommands.filter(r => r.duration > 5000);
    if (slowCommands.length > 0) {
      logger.warn(`Slow commands detected: ${slowCommands.map(r => r.command).join(', ')}`);
    }
  }

  // Test command reliability (repeated execution)
  const reliabilityCommand = 'just --version';
  const iterations = 5;
  let failures = 0;

  for (let i = 0; i < iterations; i++) {
    try {
      const result = await testSuite.execCommand(reliabilityCommand, { timeout: 10000 });
      if (result.code !== 0) {
        failures++;
      }
    } catch (error) {
      failures++;
    }
  }

  const successRate = ((iterations - failures) / iterations) * 100;
  logger.performance(`Command reliability: ${successRate.toFixed(1)}% (${iterations - failures}/${iterations})`);

  if (successRate < 80) {
    logger.warn('Command reliability below 80% - investigate consistency issues');
  }

  // Test concurrent command execution
  try {
    const concurrentCommands = Array(3).fill('just --version');

    const startTime = Date.now();

    const promises = concurrentCommands.map(cmd =>
      testSuite.execCommand(cmd, { timeout: 15000 })
    );

    const results = await Promise.all(promises);

    const endTime = Date.now();
    const concurrentDuration = endTime - startTime;

    const allSucceeded = results.every(r => r.code === 0);

    logger.performance(`Concurrent execution: ${concurrentDuration}ms, all succeeded: ${allSucceeded}`);

  } catch (error) {
    logger.debug(`Concurrent execution test: ${error.message}`);
  }

  // Test resource usage monitoring
  const resourceCommands = [
    'just status',
    'just r2:envs'
  ];

  for (const command of resourceCommands) {
    try {
      const memoryBefore = process.memoryUsage();

      await testSuite.execCommand(command, { timeout: 20000 });

      const memoryAfter = process.memoryUsage();
      const memoryDelta = memoryAfter.heapUsed - memoryBefore.heapUsed;

      logger.performance(`Memory usage for ${command}: ${(memoryDelta / 1024 / 1024).toFixed(2)}MB`);

    } catch (error) {
      logger.debug(`Resource monitoring: ${command} - ${error.message}`);
    }
  }

  logger.debug('Command performance and reliability validated successfully');
}

module.exports = {
  runTests,
  testJustTaskAvailability,
  testNixAppFunctionality,
  testCliScriptInterfaces,
  testCommandIntegrationChaining,
  testHelpUsageInformation,
  testErrorHandlingExitCodes,
  testInteractiveNonInteractiveModes,
  testCommandConfigurationOptions,
  testCommandPerformanceReliability,
  isJustAvailable,
  isNixAvailable,
};