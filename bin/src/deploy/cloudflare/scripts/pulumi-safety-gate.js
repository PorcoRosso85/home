#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * Pulumi Safety Gate Script
 *
 * Implements safety measures for Pulumi operations by enforcing prerequisites
 * before allowing destructive operations like apply and destroy.
 *
 * Features:
 * - Enforces res:diff=0 check before cf:apply operations
 * - Validates SOT state consistency before infrastructure changes
 * - Provides detailed error messages and remediation steps
 * - SOLID responsibility separation: plan (CI) vs apply/destroy (manual)
 * - Safety-first approach with explicit confirmation requirements
 *
 * Usage:
 *   pulumi-safety-gate --operation apply --env dev
 *   pulumi-safety-gate --operation destroy --env prod --force
 *   pulumi-safety-gate --operation plan --env stg
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Import diff-state for drift detection
const diffState = require('./diff-state.js');

// Configuration constants
const CONFIG = {
  supportedEnvironments: ['dev', 'stg', 'prod'],
  supportedOperations: ['plan', 'apply', 'destroy'],

  // Exit codes for different scenarios
  exitCodes: {
    SUCCESS: 0,              // Operation allowed to proceed
    SAFETY_VIOLATION: 1,     // Safety gate blocked operation
    DRIFT_DETECTED: 2,       // Configuration drift found
    VALIDATION_ERROR: 3,     // Input validation error
    EXECUTION_ERROR: 4       // Script execution error
  },

  // Safety requirements by operation
  safetyRequirements: {
    plan: {
      requiresAuth: true,
      requiresSOT: true,
      requiresDriftCheck: false,
      allowInCI: true
    },
    apply: {
      requiresAuth: true,
      requiresSOT: true,
      requiresDriftCheck: true,
      allowInCI: false
    },
    destroy: {
      requiresAuth: true,
      requiresSOT: true,
      requiresDriftCheck: true,
      allowInCI: false
    }
  }
};

// CLI state
let globalOptions = {
  operation: 'plan',
  environment: 'dev',
  force: false,
  verbose: false,
  quiet: false,
  help: false
};

/**
 * Display usage information and safety documentation
 */
function showHelp() {
  console.log(`
Pulumi Safety Gate - Infrastructure Change Protection
===================================================

Enforces safety measures and prerequisites before allowing Pulumi operations.
Implements SOLID responsibility separation and safety-first approach.

USAGE:
  pulumi-safety-gate [OPTIONS]

OPTIONS:
  --operation OP         Pulumi operation (plan/apply/destroy) [default: plan]
  --env ENV             Environment to operate on (dev/stg/prod) [default: dev]
  --force               Skip interactive confirmations (dangerous!)
  --verbose             Enable verbose output and debugging
  --quiet               Suppress output except critical errors
  --help                Show this help message

SAFETY REQUIREMENTS BY OPERATION:

  plan (CI/CD Safe):
  - ✅ Wrangler authentication required
  - ✅ SOT configuration must exist
  - ✅ Can run in CI/CD environments
  - ❌ No drift check required (read-only operation)

  apply (Manual Only):
  - ✅ Wrangler authentication required
  - ✅ SOT configuration must exist
  - ✅ res:diff=0 check MUST pass (zero configuration drift)
  - ❌ Blocked in CI/CD environments (manual operation only)
  - ⚠️  Interactive confirmation required

  destroy (Manual Only):
  - ✅ Wrangler authentication required
  - ✅ SOT configuration must exist
  - ✅ res:diff=0 check MUST pass (zero configuration drift)
  - ❌ Blocked in CI/CD environments (manual operation only)
  - ⚠️  Interactive confirmation required

EXIT CODES:
  0  - Operation allowed to proceed
  1  - Safety gate blocked operation (requirements not met)
  2  - Configuration drift detected (diff != 0)
  3  - Input validation error (invalid arguments)
  4  - Script execution error (internal error)

EXAMPLES:
  # CI/CD safe operations
  pulumi-safety-gate --operation plan --env dev
  pulumi-safety-gate --operation plan --env prod

  # Manual operations (require zero drift)
  pulumi-safety-gate --operation apply --env dev
  pulumi-safety-gate --operation destroy --env prod

  # Force mode (bypasses confirmations - dangerous!)
  pulumi-safety-gate --operation apply --env dev --force

SAFETY PHILOSOPHY:
  This script implements a safety-first approach to infrastructure management:

  1. SOLID Responsibility Separation:
     - plan: CI/CD automated testing and validation
     - apply/destroy: Manual execution with strict prerequisites

  2. Zero-Drift Requirement:
     - apply/destroy operations require res:diff=0
     - Ensures SOT and remote state are synchronized before changes
     - Prevents accidental overwrites or inconsistent states

  3. Environment Protection:
     - Explicit authentication verification
     - SOT configuration validation
     - Interactive confirmations for destructive operations

  4. CI/CD Integration:
     - plan operations are CI/CD friendly
     - apply/destroy are blocked in automated environments
     - Clear separation of concerns

REMEDIATION STEPS:
  If safety gate blocks your operation:

  1. For authentication issues:
     wrangler login

  2. For missing SOT configuration:
     # Create spec/{env}/cloudflare.yaml with your infrastructure definition

  3. For configuration drift (diff != 0):
     just res:diff {env}                    # Identify differences
     # Either update SOT or fix remote state, then retry

  4. For CI/CD blocking:
     # apply/destroy must be run manually, not in CI/CD
`);
}

/**
 * Parse command line arguments
 */
function parseArguments() {
  const args = process.argv.slice(2);

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--operation':
        globalOptions.operation = args[++i];
        if (!CONFIG.supportedOperations.includes(globalOptions.operation)) {
          console.error(`❌ Error: Unsupported operation "${globalOptions.operation}"`);
          console.error(`   Supported: ${CONFIG.supportedOperations.join(', ')}`);
          process.exit(CONFIG.exitCodes.VALIDATION_ERROR);
        }
        break;
      case '--env':
        globalOptions.environment = args[++i];
        if (!CONFIG.supportedEnvironments.includes(globalOptions.environment)) {
          console.error(`❌ Error: Unsupported environment "${globalOptions.environment}"`);
          console.error(`   Supported: ${CONFIG.supportedEnvironments.join(', ')}`);
          process.exit(CONFIG.exitCodes.VALIDATION_ERROR);
        }
        break;
      case '--force':
        globalOptions.force = true;
        break;
      case '--verbose':
        globalOptions.verbose = true;
        break;
      case '--quiet':
        globalOptions.quiet = true;
        break;
      case '--help':
        globalOptions.help = true;
        break;
      default:
        if (arg.startsWith('--')) {
          console.error(`❌ Error: Unknown option "${arg}"`);
          console.error('   Use --help to see available options');
          process.exit(CONFIG.exitCodes.VALIDATION_ERROR);
        }
        break;
    }
  }
}

/**
 * Log message if verbose mode is enabled
 */
function verbose(message) {
  if (globalOptions.verbose && !globalOptions.quiet) {
    console.log(`🔍 ${message}`);
  }
}

/**
 * Log info message unless quiet mode is enabled
 */
function info(message) {
  if (!globalOptions.quiet) {
    console.log(message);
  }
}

/**
 * Log error message (always shown)
 */
function error(message) {
  console.error(`❌ ${message}`);
}

/**
 * Log warning message unless quiet mode is enabled
 */
function warn(message) {
  if (!globalOptions.quiet) {
    console.log(`⚠️ ${message}`);
  }
}

/**
 * Check if running in CI/CD environment
 */
function isCI() {
  return !!(
    process.env.CI ||
    process.env.CONTINUOUS_INTEGRATION ||
    process.env.GITHUB_ACTIONS ||
    process.env.GITLAB_CI ||
    process.env.JENKINS_URL ||
    process.env.BUILD_NUMBER
  );
}

/**
 * Verify Wrangler authentication
 */
async function checkWranglerAuth() {
  verbose('Checking Wrangler authentication...');

  try {
    const result = execSync('wrangler whoami', {
      encoding: 'utf8',
      stdio: 'pipe',
      timeout: 10000
    });

    verbose('Wrangler authentication verified');
    return true;
  } catch (err) {
    error('Wrangler authentication failed');
    if (globalOptions.verbose) {
      console.error(`   Command output: ${err.message}`);
    }
    return false;
  }
}

/**
 * Verify SOT configuration exists
 */
async function checkSOTConfiguration() {
  verbose(`Checking SOT configuration for environment: ${globalOptions.environment}`);

  const sotPath = `spec/${globalOptions.environment}/cloudflare.yaml`;

  if (!fs.existsSync(sotPath)) {
    error(`SOT configuration not found: ${sotPath}`);
    info('   Create SOT configuration with your infrastructure definition');
    return false;
  }

  // Validate SOT configuration can be loaded
  try {
    // Use existing SOPS YAML helper to load and validate
    const sopsYaml = require('../helpers/sops-yaml.js');
    await sopsYaml.getSOTConfig(globalOptions.environment, {
      skipValidation: false
    });

    verbose('SOT configuration loaded and validated successfully');
    return true;
  } catch (err) {
    error(`SOT configuration validation failed: ${err.message}`);
    return false;
  }
}

/**
 * Perform drift check (res:diff=0 validation)
 */
async function checkConfigurationDrift() {
  verbose('Performing configuration drift check...');

  try {
    // Execute drift detection using the existing diff-state script
    const command = `node ${path.join(__dirname, 'diff-state.js')} --env ${globalOptions.environment} --format summary --quiet`;

    if (globalOptions.verbose) {
      verbose(`Executing: ${command}`);
    }

    execSync(command, {
      stdio: globalOptions.verbose ? 'inherit' : 'pipe',
      timeout: 60000 // 60 second timeout
    });

    verbose('Configuration drift check passed: diff=0');
    return true;
  } catch (err) {
    const exitCode = err.status || 1;

    if (exitCode === 1) {
      error('Configuration drift detected (diff != 0)');
      info('   Run `just res:diff ${env}` to see detailed differences');
      info('   Fix SOT configuration or remote state before retrying');
    } else {
      error(`Drift check failed with exit code ${exitCode}`);
      if (globalOptions.verbose) {
        console.error(`   Error: ${err.message}`);
      }
    }

    return false;
  }
}

/**
 * Interactive confirmation for destructive operations
 */
async function requestConfirmation() {
  if (globalOptions.force) {
    warn('Force mode enabled - skipping confirmation');
    return true;
  }

  const operation = globalOptions.operation;
  const environment = globalOptions.environment;

  console.log(`\n⚠️  DESTRUCTIVE OPERATION CONFIRMATION`);
  console.log(`=====================================`);
  console.log(`Operation: ${operation}`);
  console.log(`Environment: ${environment}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log(``);

  if (operation === 'destroy') {
    console.log(`🚨 WARNING: This will DESTROY infrastructure resources!`);
    console.log(`   This action is IRREVERSIBLE and may cause data loss.`);
  } else if (operation === 'apply') {
    console.log(`🔧 This will MODIFY infrastructure resources.`);
    console.log(`   Changes will be applied to live environment.`);
  }

  console.log(``);
  console.log(`Prerequisites verified:`);
  console.log(`✅ Wrangler authentication`);
  console.log(`✅ SOT configuration exists`);
  console.log(`✅ Configuration drift check (diff=0)`);
  console.log(``);

  // Simple confirmation for Node.js script
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    readline.question(`Type "yes" to proceed with ${operation} operation: `, (answer) => {
      readline.close();
      resolve(answer.toLowerCase() === 'yes');
    });
  });
}

/**
 * Main safety gate validation
 */
async function validateSafetyRequirements() {
  const operation = globalOptions.operation;
  const requirements = CONFIG.safetyRequirements[operation];

  verbose(`Validating safety requirements for operation: ${operation}`);

  // Check CI/CD environment restrictions
  if (!requirements.allowInCI && isCI()) {
    error(`Operation '${operation}' is not allowed in CI/CD environments`);
    info('   This operation requires manual execution for safety');
    info('   Use plan operation for CI/CD validation');
    return false;
  }

  // Check Wrangler authentication
  if (requirements.requiresAuth) {
    if (!(await checkWranglerAuth())) {
      info('   Remediation: Run `wrangler login` to authenticate');
      return false;
    }
  }

  // Check SOT configuration
  if (requirements.requiresSOT) {
    if (!(await checkSOTConfiguration())) {
      info(`   Remediation: Create spec/${globalOptions.environment}/cloudflare.yaml`);
      return false;
    }
  }

  // Check configuration drift (critical for apply/destroy)
  if (requirements.requiresDriftCheck) {
    if (!(await checkConfigurationDrift())) {
      info('   Remediation: Fix configuration drift before retrying');
      info(`   Run: just res:diff ${globalOptions.environment}`);
      return false;
    }
  }

  // Interactive confirmation for destructive operations
  if (['apply', 'destroy'].includes(operation)) {
    if (!(await requestConfirmation())) {
      info('Operation cancelled by user');
      return false;
    }
  }

  return true;
}

/**
 * Main execution function
 */
async function main() {
  try {
    parseArguments();

    if (globalOptions.help) {
      showHelp();
      return;
    }

    info(`🛡️ Pulumi Safety Gate - ${globalOptions.operation} operation`);
    info(`Environment: ${globalOptions.environment}`);

    if (isCI()) {
      info(`Detected CI/CD environment`);
    }

    info(``);

    // Validate safety requirements
    const safetyCheckPassed = await validateSafetyRequirements();

    if (!safetyCheckPassed) {
      error(`Safety gate BLOCKED ${globalOptions.operation} operation`);
      info('');
      info('🎯 Safety Requirements:');

      const requirements = CONFIG.safetyRequirements[globalOptions.operation];

      if (requirements.requiresAuth) {
        info('   ✅ Wrangler authentication');
      }
      if (requirements.requiresSOT) {
        info('   ✅ SOT configuration exists');
      }
      if (requirements.requiresDriftCheck) {
        info('   ✅ Configuration drift check (diff=0)');
      }
      if (!requirements.allowInCI) {
        info('   ✅ Manual execution (not CI/CD)');
      }

      info('');
      info('📋 Next Steps:');
      info('   1. Address the failed requirements above');
      info('   2. Re-run the safety gate check');
      info('   3. Proceed with Pulumi operation');

      process.exit(CONFIG.exitCodes.SAFETY_VIOLATION);
    }

    info(`✅ Safety gate PASSED - ${globalOptions.operation} operation authorized`);
    info('');
    info('🚀 Pulumi operation can proceed safely');
    info(`   Operation: ${globalOptions.operation}`);
    info(`   Environment: ${globalOptions.environment}`);
    info(`   Timestamp: ${new Date().toISOString()}`);

    process.exit(CONFIG.exitCodes.SUCCESS);

  } catch (err) {
    error(`Fatal error: ${err.message}`);
    if (globalOptions.verbose) {
      console.error(err.stack);
    }
    process.exit(CONFIG.exitCodes.EXECUTION_ERROR);
  }
}

// Execute if run directly
if (require.main === module) {
  main();
}

// Export for testing
module.exports = {
  validateSafetyRequirements,
  checkWranglerAuth,
  checkSOTConfiguration,
  checkConfigurationDrift,
  isCI,
  CONFIG
};