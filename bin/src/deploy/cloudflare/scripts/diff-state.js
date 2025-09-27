#!/usr/bin/env -S bash -c 'exec "${NODE:-node}" "$0" "$@"'

/**
 * SOT State Comparison and Diff Detection Script
 *
 * Compares SOT (Single Source of Truth) configuration from spec/{env}/cloudflare.yaml
 * with actual remote state fetched from Cloudflare APIs. Detects drift and provides
 * detailed reporting with non-zero exit codes for CI/CD integration.
 *
 * Features:
 * - SOT vs Remote state comparison
 * - R2 bucket configuration diff (name, binding)
 * - Workers basic attribute comparison (name, script)
 * - Structured diff reporting with detailed explanations
 * - Non-zero exit codes for detected drift
 * - CI/CD friendly output formatting
 * - Comprehensive error handling and validation
 *
 * Usage:
 *   diff-state --env dev
 *   diff-state --env prod --verbose
 *   diff-state --env stg --format json --output ./reports/
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Import helper modules
const sopsYaml = require('../helpers/sops-yaml.js');
const fetchRemoteState = require('./fetch-remote-state.js');

// Configuration constants
const CONFIG = {
  supportedEnvironments: ['dev', 'stg', 'prod'],
  defaultOutputDir: './generated',
  outputFilename: 'diff-report.json',

  // Exit codes for different scenarios
  exitCodes: {
    SUCCESS: 0,           // No differences found
    DRIFT_DETECTED: 1,    // Configuration drift detected
    SOT_ERROR: 2,        // SOT configuration error
    REMOTE_ERROR: 3,     // Remote state fetch error
    COMPARISON_ERROR: 4, // Comparison logic error
    VALIDATION_ERROR: 5  // Input validation error
  },

  // Comparison settings
  comparison: {
    ignoreFields: ['timestamp', 'account'], // Fields to ignore in comparison
    requireExactMatch: true,                 // Require exact matches vs subset matching
    caseSensitive: true                     // Case sensitive string comparisons
  }
};

// CLI state
let globalOptions = {
  environment: 'dev',
  outputPath: null,
  outputFormat: 'detailed',
  isVerbose: false,
  isQuiet: false,
  isDryRun: false,
  help: false
};

/**
 * Display usage information and examples
 */
function showHelp() {
  console.log(`
SOT State Comparison and Diff Detection
=======================================

Compares SOT configuration with actual Cloudflare remote state and reports
any configuration drift. Returns non-zero exit codes when differences are found.

USAGE:
  diff-state [OPTIONS]

OPTIONS:
  --env ENV              Environment to compare (dev/stg/prod) [default: dev]
  --output PATH          Output directory for diff reports [default: ./generated]
  --format FORMAT        Output format (detailed/json/summary) [default: detailed]
  --verbose              Enable verbose output and debugging
  --quiet                Suppress output except critical errors
  --dry-run              Show what would be compared without executing
  --help                 Show this help message

EXIT CODES:
  0  - No differences found (SOT and remote state match)
  1  - Configuration drift detected (differences found)
  2  - SOT configuration error (cannot read/parse SOT)
  3  - Remote state fetch error (cannot fetch from Cloudflare)
  4  - Comparison logic error (internal error during comparison)
  5  - Input validation error (invalid arguments/environment)

EXAMPLES:
  # Check dev environment for drift
  diff-state --env dev

  # Detailed comparison with verbose output
  diff-state --env prod --verbose --format detailed

  # Generate JSON report for CI/CD
  diff-state --env stg --format json --output ./reports/

  # Quick summary check
  diff-state --env dev --format summary

COMPARISON SCOPE:
  The script compares the following elements:

  R2 Buckets:
  - Bucket names (exact match required)
  - Binding names (exact match required)

  Workers:
  - Worker names (exact match required)
  - Script references (basic validation)

  Note: Account information and timestamps are ignored in comparisons.

INTEGRATION:
  This script is designed for CI/CD integration:
  - Returns exit code 1 when drift is detected
  - Provides machine-readable JSON output
  - Supports quiet mode for automated scripts
  - Generates detailed reports for manual review
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
      case '--env':
        globalOptions.environment = args[++i];
        if (!CONFIG.supportedEnvironments.includes(globalOptions.environment)) {
          console.error(`❌ Error: Unsupported environment "${globalOptions.environment}"`);
          console.error(`   Supported: ${CONFIG.supportedEnvironments.join(', ')}`);
          process.exit(CONFIG.exitCodes.VALIDATION_ERROR);
        }
        break;
      case '--output':
        globalOptions.outputPath = args[++i];
        break;
      case '--format':
        globalOptions.outputFormat = args[++i];
        if (!['detailed', 'json', 'summary'].includes(globalOptions.outputFormat)) {
          console.error(`❌ Error: Unsupported format "${globalOptions.outputFormat}"`);
          console.error(`   Supported: detailed, json, summary`);
          process.exit(CONFIG.exitCodes.VALIDATION_ERROR);
        }
        break;
      case '--verbose':
        globalOptions.isVerbose = true;
        break;
      case '--quiet':
        globalOptions.isQuiet = true;
        break;
      case '--dry-run':
        globalOptions.isDryRun = true;
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
  if (globalOptions.isVerbose && !globalOptions.isQuiet) {
    console.log(`🔍 ${message}`);
  }
}

/**
 * Log info message unless quiet mode is enabled
 */
function info(message) {
  if (!globalOptions.isQuiet) {
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
 * Load SOT configuration for the specified environment
 */
async function loadSOTConfig(environment) {
  verbose(`Loading SOT configuration for environment: ${environment}`);

  try {
    const sotConfig = await sopsYaml.getSOTConfig(environment, {
      skipValidation: false // Enable schema validation
    });

    verbose(`SOT configuration loaded successfully`);
    verbose(`SOT has ${sotConfig.r2?.buckets?.length || 0} R2 buckets`);
    verbose(`SOT has ${sotConfig.workers?.length || 0} workers`);

    return sotConfig;
  } catch (error) {
    throw new Error(`Failed to load SOT configuration: ${error.message}`);
  }
}

/**
 * Load remote state for the specified environment
 */
async function loadRemoteState(environment) {
  verbose(`Fetching remote state for environment: ${environment}`);

  try {
    // Use the fetch-remote-state script to get current state
    const outputDir = globalOptions.outputPath || CONFIG.defaultOutputDir;
    const remoteStateFile = path.join(outputDir, `${environment}-remote-state.json`);

    // Execute fetch-remote-state script
    const command = `node ${path.join(__dirname, 'fetch-remote-state.js')} --env ${environment} --output ${outputDir} --format json`;

    if (globalOptions.isVerbose) {
      verbose(`Executing: ${command}`);
    }

    execSync(command, {
      stdio: globalOptions.isVerbose ? 'inherit' : 'pipe',
      timeout: 60000 // 60 second timeout
    });

    // Read the generated remote state file
    if (!fs.existsSync(remoteStateFile)) {
      throw new Error(`Remote state file not generated: ${remoteStateFile}`);
    }

    const remoteStateContent = fs.readFileSync(remoteStateFile, 'utf8');
    const remoteState = JSON.parse(remoteStateContent);

    verbose(`Remote state loaded successfully`);
    verbose(`Remote has ${remoteState.r2?.buckets?.length || 0} R2 buckets`);
    verbose(`Remote has ${remoteState.workers?.length || 0} workers`);

    return remoteState;
  } catch (error) {
    if (error.message.includes('wrangler')) {
      throw new Error(`Failed to fetch remote state - check wrangler authentication: ${error.message}`);
    }
    throw new Error(`Failed to load remote state: ${error.message}`);
  }
}

/**
 * Compare two arrays of objects by a key field
 */
function compareArraysByKey(sotArray, remoteArray, keyField, description) {
  const differences = {
    missing: [],      // Items in SOT but not in remote
    extra: [],        // Items in remote but not in SOT
    modified: []      // Items that exist in both but with different properties
  };

  const sotMap = new Map();
  const remoteMap = new Map();

  // Index SOT items by key field
  if (sotArray && Array.isArray(sotArray)) {
    sotArray.forEach(item => {
      if (item[keyField]) {
        sotMap.set(item[keyField], item);
      }
    });
  }

  // Index remote items by key field
  if (remoteArray && Array.isArray(remoteArray)) {
    remoteArray.forEach(item => {
      if (item[keyField]) {
        remoteMap.set(item[keyField], item);
      }
    });
  }

  // Find missing items (in SOT but not in remote)
  sotMap.forEach((sotItem, key) => {
    if (!remoteMap.has(key)) {
      differences.missing.push({
        key,
        expected: sotItem,
        type: description
      });
    }
  });

  // Find extra items (in remote but not in SOT)
  remoteMap.forEach((remoteItem, key) => {
    if (!sotMap.has(key)) {
      differences.extra.push({
        key,
        actual: remoteItem,
        type: description
      });
    }
  });

  // Find modified items (exist in both but different)
  sotMap.forEach((sotItem, key) => {
    const remoteItem = remoteMap.get(key);
    if (remoteItem) {
      const itemDiffs = compareObjects(sotItem, remoteItem, [`${description}:${key}`]);
      if (itemDiffs.length > 0) {
        differences.modified.push({
          key,
          expected: sotItem,
          actual: remoteItem,
          differences: itemDiffs,
          type: description
        });
      }
    }
  });

  return differences;
}

/**
 * Compare two objects and return differences
 */
function compareObjects(expected, actual, path = []) {
  const differences = [];

  // Get all unique keys from both objects
  const allKeys = new Set([
    ...Object.keys(expected || {}),
    ...Object.keys(actual || {})
  ]);

  allKeys.forEach(key => {
    const currentPath = [...path, key].join('.');
    const expectedValue = expected?.[key];
    const actualValue = actual?.[key];

    // Skip ignored fields
    if (CONFIG.comparison.ignoreFields.includes(key)) {
      return;
    }

    if (expectedValue !== actualValue) {
      // Handle different comparison strategies
      if (typeof expectedValue === 'string' && typeof actualValue === 'string') {
        const expectedComp = CONFIG.comparison.caseSensitive ? expectedValue : expectedValue.toLowerCase();
        const actualComp = CONFIG.comparison.caseSensitive ? actualValue : actualValue.toLowerCase();

        if (expectedComp !== actualComp) {
          differences.push({
            path: currentPath,
            expected: expectedValue,
            actual: actualValue,
            type: 'value_mismatch'
          });
        }
      } else if (expectedValue !== actualValue) {
        differences.push({
          path: currentPath,
          expected: expectedValue,
          actual: actualValue,
          type: 'value_mismatch'
        });
      }
    }
  });

  return differences;
}

/**
 * Perform comprehensive state comparison
 */
function compareStates(sotConfig, remoteState) {
  verbose(`Starting comprehensive state comparison`);

  const comparisonResult = {
    environment: globalOptions.environment,
    timestamp: new Date().toISOString(),
    hasDifferences: false,
    summary: {
      totalDifferences: 0,
      r2Differences: 0,
      workerDifferences: 0
    },
    differences: {
      r2: {
        buckets: { missing: [], extra: [], modified: [] }
      },
      workers: { missing: [], extra: [], modified: [] }
    },
    metadata: {
      sotVersion: sotConfig.version || 'unknown',
      remoteAccount: remoteState.account?.name || 'unknown',
      comparedAt: new Date().toISOString()
    }
  };

  try {
    // Compare R2 buckets
    verbose(`Comparing R2 buckets...`);
    const r2Diffs = compareArraysByKey(
      sotConfig.r2?.buckets,
      remoteState.r2?.buckets,
      'name',
      'R2 bucket'
    );
    comparisonResult.differences.r2.buckets = r2Diffs;

    const r2DiffCount = r2Diffs.missing.length + r2Diffs.extra.length + r2Diffs.modified.length;
    comparisonResult.summary.r2Differences = r2DiffCount;

    verbose(`R2 comparison complete: ${r2DiffCount} differences found`);

    // Compare Workers
    verbose(`Comparing Workers...`);
    const workerDiffs = compareArraysByKey(
      sotConfig.workers,
      remoteState.workers,
      'name',
      'Worker'
    );
    comparisonResult.differences.workers = workerDiffs;

    const workerDiffCount = workerDiffs.missing.length + workerDiffs.extra.length + workerDiffs.modified.length;
    comparisonResult.summary.workerDifferences = workerDiffCount;

    verbose(`Worker comparison complete: ${workerDiffCount} differences found`);

    // Calculate totals
    comparisonResult.summary.totalDifferences = r2DiffCount + workerDiffCount;
    comparisonResult.hasDifferences = comparisonResult.summary.totalDifferences > 0;

    verbose(`Comparison complete: ${comparisonResult.summary.totalDifferences} total differences`);

    return comparisonResult;

  } catch (error) {
    throw new Error(`Comparison failed: ${error.message}`);
  }
}

/**
 * Generate detailed human-readable report
 */
function generateDetailedReport(comparisonResult) {
  const lines = [];

  lines.push(`🔍 SOT State Comparison Report`);
  lines.push(`==============================`);
  lines.push(``);
  lines.push(`Environment: ${comparisonResult.environment}`);
  lines.push(`Compared at: ${comparisonResult.metadata.comparedAt}`);
  lines.push(`SOT Version: ${comparisonResult.metadata.sotVersion}`);
  lines.push(`Remote Account: ${comparisonResult.metadata.remoteAccount}`);
  lines.push(``);

  if (!comparisonResult.hasDifferences) {
    lines.push(`✅ SUCCESS: No configuration drift detected`);
    lines.push(`   SOT configuration matches remote state perfectly.`);
    lines.push(``);
    return lines.join('\n');
  }

  lines.push(`❌ DRIFT DETECTED: Configuration differences found`);
  lines.push(`   Total differences: ${comparisonResult.summary.totalDifferences}`);
  lines.push(`   R2 differences: ${comparisonResult.summary.r2Differences}`);
  lines.push(`   Worker differences: ${comparisonResult.summary.workerDifferences}`);
  lines.push(``);

  // R2 Bucket differences
  if (comparisonResult.summary.r2Differences > 0) {
    lines.push(`📦 R2 Bucket Differences:`);
    lines.push(`------------------------`);

    const r2Diffs = comparisonResult.differences.r2.buckets;

    if (r2Diffs.missing.length > 0) {
      lines.push(`   Missing buckets (defined in SOT but not in remote):`);
      r2Diffs.missing.forEach(item => {
        lines.push(`   - ${item.key} (binding: ${item.expected.binding || 'N/A'})`);
      });
      lines.push(``);
    }

    if (r2Diffs.extra.length > 0) {
      lines.push(`   Extra buckets (in remote but not in SOT):`);
      r2Diffs.extra.forEach(item => {
        lines.push(`   - ${item.key} (binding: ${item.actual.binding || 'N/A'})`);
      });
      lines.push(``);
    }

    if (r2Diffs.modified.length > 0) {
      lines.push(`   Modified buckets (different properties):`);
      r2Diffs.modified.forEach(item => {
        lines.push(`   - ${item.key}:`);
        item.differences.forEach(diff => {
          lines.push(`     * ${diff.path}: expected "${diff.expected}", got "${diff.actual}"`);
        });
      });
      lines.push(``);
    }
  }

  // Worker differences
  if (comparisonResult.summary.workerDifferences > 0) {
    lines.push(`⚙️ Worker Differences:`);
    lines.push(`---------------------`);

    const workerDiffs = comparisonResult.differences.workers;

    if (workerDiffs.missing.length > 0) {
      lines.push(`   Missing workers (defined in SOT but not deployed):`);
      workerDiffs.missing.forEach(item => {
        lines.push(`   - ${item.key} (script: ${item.expected.script || 'N/A'})`);
      });
      lines.push(``);
    }

    if (workerDiffs.extra.length > 0) {
      lines.push(`   Extra workers (deployed but not in SOT):`);
      workerDiffs.extra.forEach(item => {
        lines.push(`   - ${item.key} (script: ${item.actual.script || 'N/A'})`);
      });
      lines.push(``);
    }

    if (workerDiffs.modified.length > 0) {
      lines.push(`   Modified workers (different properties):`);
      workerDiffs.modified.forEach(item => {
        lines.push(`   - ${item.key}:`);
        item.differences.forEach(diff => {
          lines.push(`     * ${diff.path}: expected "${diff.expected}", got "${diff.actual}"`);
        });
      });
      lines.push(``);
    }
  }

  lines.push(`🎯 Recommended Actions:`);
  lines.push(`----------------------`);
  if (comparisonResult.differences.r2.buckets.missing.length > 0) {
    lines.push(`   - Create missing R2 buckets in Cloudflare`);
  }
  if (comparisonResult.differences.r2.buckets.extra.length > 0) {
    lines.push(`   - Review extra R2 buckets (consider adding to SOT or removing)`);
  }
  if (comparisonResult.differences.workers.missing.length > 0) {
    lines.push(`   - Deploy missing workers to Cloudflare`);
  }
  if (comparisonResult.differences.workers.extra.length > 0) {
    lines.push(`   - Review extra workers (consider adding to SOT or removing)`);
  }
  lines.push(`   - Update SOT configuration to match intended state`);
  lines.push(`   - Re-run comparison after making changes`);
  lines.push(``);

  return lines.join('\n');
}

/**
 * Generate summary report
 */
function generateSummaryReport(comparisonResult) {
  if (!comparisonResult.hasDifferences) {
    return `✅ ${comparisonResult.environment}: No drift detected (${comparisonResult.summary.totalDifferences} differences)`;
  }

  return `❌ ${comparisonResult.environment}: Drift detected (${comparisonResult.summary.totalDifferences} differences: ${comparisonResult.summary.r2Differences} R2, ${comparisonResult.summary.workerDifferences} workers)`;
}

/**
 * Write comparison report to file
 */
function writeComparisonReport(comparisonResult) {
  const outputDir = globalOptions.outputPath || CONFIG.defaultOutputDir;

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    if (globalOptions.isDryRun) {
      info(`[DRY RUN] Would create directory: ${outputDir}`);
    } else {
      fs.mkdirSync(outputDir, { recursive: true });
      verbose(`Created output directory: ${outputDir}`);
    }
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${comparisonResult.environment}-diff-report-${timestamp}.json`;
  const outputPath = path.join(outputDir, filename);

  if (globalOptions.isDryRun) {
    info(`[DRY RUN] Would write report to: ${outputPath}`);
    return outputPath;
  }

  try {
    fs.writeFileSync(outputPath, JSON.stringify(comparisonResult, null, 2));
    verbose(`Comparison report written to: ${outputPath}`);
    return outputPath;
  } catch (error) {
    error(`Failed to write comparison report: ${error.message}`);
    return null;
  }
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

    verbose(`Starting SOT state comparison for environment: ${globalOptions.environment}`);

    if (globalOptions.isDryRun) {
      info(`[DRY RUN] Would compare SOT vs remote state for ${globalOptions.environment}`);
      return;
    }

    // Load SOT configuration
    let sotConfig;
    try {
      sotConfig = await loadSOTConfig(globalOptions.environment);
    } catch (error) {
      error(`SOT configuration error: ${error.message}`);
      process.exit(CONFIG.exitCodes.SOT_ERROR);
    }

    // Load remote state
    let remoteState;
    try {
      remoteState = await loadRemoteState(globalOptions.environment);
    } catch (error) {
      error(`Remote state error: ${error.message}`);
      process.exit(CONFIG.exitCodes.REMOTE_ERROR);
    }

    // Perform comparison
    let comparisonResult;
    try {
      comparisonResult = compareStates(sotConfig, remoteState);
    } catch (error) {
      error(`Comparison error: ${error.message}`);
      process.exit(CONFIG.exitCodes.COMPARISON_ERROR);
    }

    // Generate and output report
    try {
      let outputContent;

      switch (globalOptions.outputFormat) {
        case 'json':
          outputContent = JSON.stringify(comparisonResult, null, 2);
          break;
        case 'summary':
          outputContent = generateSummaryReport(comparisonResult);
          break;
        case 'detailed':
        default:
          outputContent = generateDetailedReport(comparisonResult);
          break;
      }

      // Output to console
      if (!globalOptions.isQuiet) {
        console.log(outputContent);
      }

      // Write report file if requested
      if (globalOptions.outputFormat === 'json' || globalOptions.isVerbose) {
        writeComparisonReport(comparisonResult);
      }

    } catch (error) {
      error(`Report generation error: ${error.message}`);
      process.exit(CONFIG.exitCodes.COMPARISON_ERROR);
    }

    // Exit with appropriate code
    if (comparisonResult.hasDifferences) {
      verbose(`Exiting with code ${CONFIG.exitCodes.DRIFT_DETECTED} (drift detected)`);
      process.exit(CONFIG.exitCodes.DRIFT_DETECTED);
    } else {
      verbose(`Exiting with code ${CONFIG.exitCodes.SUCCESS} (no drift)`);
      process.exit(CONFIG.exitCodes.SUCCESS);
    }

  } catch (error) {
    error(`Fatal error: ${error.message}`);
    if (globalOptions.isVerbose) {
      console.error(error.stack);
    }
    process.exit(CONFIG.exitCodes.COMPARISON_ERROR);
  }
}

// Execute if run directly
if (require.main === module) {
  main();
}

// Export for testing
module.exports = {
  compareStates,
  compareArraysByKey,
  compareObjects,
  loadSOTConfig,
  loadRemoteState,
  generateDetailedReport,
  generateSummaryReport,
  CONFIG
};