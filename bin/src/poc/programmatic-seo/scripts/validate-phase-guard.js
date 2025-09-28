#!/usr/bin/env node

/**
 * Phase Guard Validation Script for Programmatic SEO
 * Validates phase completion requirements and transitions
 */

const fs = require('fs');
const path = require('path');

class PhaseGuardValidator {
  constructor(projectRoot = '.') {
    this.projectRoot = projectRoot;
    this.errors = [];
    this.warnings = [];
    this.phaseStatusPath = path.join(projectRoot, 'docs', 'PHASES_STATUS.json');
    this.receiptsDir = path.join(projectRoot, 'docs', '.receipts');
  }

  validatePhaseStatusFile() {
    if (!fs.existsSync(this.phaseStatusPath)) {
      this.errors.push(`PHASES_STATUS.json not found: ${this.phaseStatusPath}`);
      return false;
    }

    try {
      const content = fs.readFileSync(this.phaseStatusPath, 'utf-8');
      const phaseStatus = JSON.parse(content);

      if (!phaseStatus.phases || typeof phaseStatus.phases !== 'object') {
        this.errors.push('Invalid PHASES_STATUS.json structure - missing phases object');
        return false;
      }

      console.log(`✓ PHASES_STATUS.json exists and is valid`);
      return phaseStatus;
    } catch (error) {
      this.errors.push(`Failed to parse PHASES_STATUS.json: ${error.message}`);
      return false;
    }
  }

  validateReceiptsDirectory() {
    if (!fs.existsSync(this.receiptsDir)) {
      this.warnings.push(`Receipts directory not found: ${this.receiptsDir}`);
      return [];
    }

    try {
      const files = fs.readdirSync(this.receiptsDir);
      const receipts = files.filter(file => file.endsWith('.done'));

      console.log(`✓ Receipts directory exists with ${receipts.length} completion receipts`);
      return receipts;
    } catch (error) {
      this.errors.push(`Failed to read receipts directory: ${error.message}`);
      return [];
    }
  }

  validatePhase(phaseId, phaseConfig, receipts) {
    console.log(`\nValidating Phase ${phaseId}:`);

    const receiptFile = `${phaseId}.done`;
    const hasReceipt = receipts.includes(receiptFile);

    // Check completion status
    if (phaseConfig.status === 'completed') {
      if (!hasReceipt) {
        this.errors.push(`Phase ${phaseId} marked as completed but no receipt found (${receiptFile})`);
        return false;
      }
      console.log(`  ✓ Phase ${phaseId} completed with receipt`);
    } else if (phaseConfig.status === 'in_progress') {
      if (hasReceipt) {
        this.warnings.push(`Phase ${phaseId} has receipt but status is still 'in_progress'`);
      }
      console.log(`  ⏳ Phase ${phaseId} in progress`);
    } else {
      console.log(`  ⏸️ Phase ${phaseId} status: ${phaseConfig.status}`);
    }

    // Validate requirements
    if (phaseConfig.requirements) {
      for (const requirement of phaseConfig.requirements) {
        this.validateRequirement(phaseId, requirement);
      }
    }

    // Validate dependencies
    if (phaseConfig.dependencies) {
      for (const depPhase of phaseConfig.dependencies) {
        if (!receipts.includes(`${depPhase}.done`)) {
          this.errors.push(`Phase ${phaseId} depends on ${depPhase} which is not completed`);
          return false;
        }
      }
      console.log(`  ✓ All dependencies satisfied`);
    }

    return true;
  }

  validateRequirement(phaseId, requirement) {
    const reqPath = path.join(this.projectRoot, requirement);

    if (fs.existsSync(reqPath)) {
      const stats = fs.statSync(reqPath);
      if (stats.isFile() && stats.size > 0) {
        console.log(`  ✓ Requirement satisfied: ${requirement}`);
        return true;
      } else if (stats.isDirectory()) {
        const files = fs.readdirSync(reqPath);
        if (files.length > 0) {
          console.log(`  ✓ Requirement satisfied: ${requirement} (${files.length} files)`);
          return true;
        } else {
          this.warnings.push(`Requirement directory is empty: ${requirement}`);
          return false;
        }
      } else {
        this.warnings.push(`Requirement file is empty: ${requirement}`);
        return false;
      }
    } else {
      this.errors.push(`Phase ${phaseId} requirement missing: ${requirement}`);
      return false;
    }
  }

  validatePhase11Specifics() {
    console.log('\nValidating Phase 1.1 specific requirements:');

    // Check for Phase 1.1 documentation
    const phase11DocPath = path.join(this.projectRoot, 'docs', 'phases', '1.1-Lite-pSEO.md');
    if (!fs.existsSync(phase11DocPath)) {
      console.log('  ℹ️ Phase 1.1 documentation not found - checking completion requirements');

      // If no docs, check critical completion requirements
      const criticalPaths = [
        'docs/.receipts/1.1.done',
        'public/sitemap.xml',
        'scripts/build-sitemap.ts',
        'scripts/build-hreflang.ts'
      ];

      for (const criticalPath of criticalPaths) {
        const fullPath = path.join(this.projectRoot, criticalPath);
        if (!fs.existsSync(fullPath)) {
          this.errors.push(`Critical Phase 1.1 requirement missing: ${criticalPath}`);
        } else {
          console.log(`  ✓ Critical requirement found: ${criticalPath}`);
        }
      }
    } else {
      console.log('  ✓ Phase 1.1 documentation exists');
    }

    // Validate flake.nix apps section
    const flakePath = path.join(this.projectRoot, 'flake.nix');
    if (fs.existsSync(flakePath)) {
      const flakeContent = fs.readFileSync(flakePath, 'utf-8');

      const requiredApps = ['build-sitemap', 'build-hreflang'];
      for (const app of requiredApps) {
        if (flakeContent.includes(`${app} =`)) {
          console.log(`  ✓ Required app found in flake.nix: ${app}`);
        } else {
          this.errors.push(`Required app missing from flake.nix: ${app}`);
        }
      }

      const requiredChecks = ['sitemap-exists', 'sitemap-validation', 'hreflang-validation'];
      for (const check of requiredChecks) {
        if (flakeContent.includes(`${check} =`)) {
          console.log(`  ✓ Required check found in flake.nix: ${check}`);
        } else {
          this.errors.push(`Required check missing from flake.nix: ${check}`);
        }
      }
    } else {
      this.errors.push('flake.nix not found');
    }
  }

  validate() {
    console.log('Phase Guard Validation for Programmatic SEO');
    console.log(`Project root: ${this.projectRoot}`);
    console.log('');

    // Load phase status
    const phaseStatus = this.validatePhaseStatusFile();
    if (!phaseStatus) {
      this.reportResults();
      return false;
    }

    // Load receipts
    const receipts = this.validateReceiptsDirectory();

    // Validate each phase
    let allPhasesValid = true;
    for (const [phaseId, phaseConfig] of Object.entries(phaseStatus.phases)) {
      if (!this.validatePhase(phaseId, phaseConfig, receipts)) {
        allPhasesValid = false;
      }
    }

    // Phase 1.1 specific validation
    this.validatePhase11Specifics();

    this.reportResults();
    return allPhasesValid && this.errors.length === 0;
  }

  reportResults() {
    console.log('');
    console.log('=== Phase Guard Validation Results ===');

    if (this.errors.length > 0) {
      console.log('❌ ERRORS:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }

    if (this.warnings.length > 0) {
      console.log('⚠️  WARNINGS:');
      this.warnings.forEach(warning => console.log(`  - ${warning}`));
    }

    if (this.errors.length === 0) {
      console.log('✅ Phase guard validation passed');
    } else {
      console.log('❌ Phase guard validation failed');
    }
  }
}

// Main execution
function main() {
  const projectRoot = process.argv[2] || '.';

  console.log('Programmatic SEO - Phase Guard Validator');
  console.log('');

  const validator = new PhaseGuardValidator(projectRoot);
  const isValid = validator.validate();

  process.exit(isValid ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { PhaseGuardValidator };
