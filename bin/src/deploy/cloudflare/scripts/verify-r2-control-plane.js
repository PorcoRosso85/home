#!/usr/bin/env node

/**
 * R2 Control Plane Operations Verification Script
 *
 * This script verifies the integrity and consistency of R2 Control Plane configurations:
 * - SOT (Single Source of Truth) settings validation
 * - Pulumi plan verification for resource generation
 * - wrangler.jsonc generation results validation
 * - Bucket name and binding consistency checks
 * - Control Plane specific configuration validation
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { execSync } from 'child_process';

class R2ControlPlaneVerifier {
    constructor(environment) {
        this.environment = environment;
        this.errors = [];
        this.warnings = [];
        this.specPath = path.join(process.cwd(), 'spec', environment, 'cloudflare.yaml');
        this.wranglerConfigPath = path.join(process.cwd(), 'generated', environment, 'wrangler.jsonc');

        console.log(`🔍 R2 Control Plane Verification for environment: ${environment}`);
        console.log(`📁 SOT Path: ${this.specPath}`);
        console.log(`📁 Generated Config Path: ${this.wranglerConfigPath}\n`);
    }

    /**
     * Load and validate SOT configuration
     */
    loadSOTConfig() {
        console.log('📋 Loading SOT Configuration...');

        if (!fs.existsSync(this.specPath)) {
            this.errors.push(`SOT configuration not found: ${this.specPath}`);
            return null;
        }

        try {
            const content = fs.readFileSync(this.specPath, 'utf8');
            const config = yaml.load(content);

            console.log(`✅ SOT configuration loaded successfully`);
            console.log(`   Version: ${config.version || 'not specified'}`);
            console.log(`   R2 Buckets: ${config.r2?.buckets?.length || 0}`);
            console.log(`   Workers: ${config.workers?.length || 0}`);
            console.log(`   Control Plane Enabled: ${config.control_plane?.enabled || false}\n`);

            return config;
        } catch (error) {
            this.errors.push(`Failed to parse SOT configuration: ${error.message}`);
            return null;
        }
    }

    /**
     * Validate R2 bucket configurations
     */
    validateR2Buckets(config) {
        console.log('🪣 Validating R2 Bucket Configurations...');

        if (!config.r2?.buckets) {
            this.errors.push('No R2 bucket configuration found in SOT');
            return;
        }

        const buckets = config.r2.buckets;
        const bucketNames = new Set();
        const bucketBindings = new Set();

        buckets.forEach((bucket, index) => {
            const bucketId = `bucket[${index}]`;

            // Validate required fields
            if (!bucket.name) {
                this.errors.push(`${bucketId}: Missing bucket name`);
            } else {
                if (bucketNames.has(bucket.name)) {
                    this.errors.push(`${bucketId}: Duplicate bucket name '${bucket.name}'`);
                } else {
                    bucketNames.add(bucket.name);
                }
            }

            if (!bucket.binding) {
                this.errors.push(`${bucketId}: Missing binding name`);
            } else {
                if (bucketBindings.has(bucket.binding)) {
                    this.errors.push(`${bucketId}: Duplicate binding name '${bucket.binding}'`);
                } else {
                    bucketBindings.add(bucket.binding);
                }
            }

            // Validate Control Plane specific settings
            if (bucket.lifecycle?.enabled) {
                if (!bucket.lifecycle.rules || bucket.lifecycle.rules.length === 0) {
                    this.warnings.push(`${bucketId}: Lifecycle enabled but no rules defined`);
                }
            }

            if (bucket.cors) {
                if (!Array.isArray(bucket.cors)) {
                    this.errors.push(`${bucketId}: CORS configuration must be an array`);
                }
            }

            console.log(`   ✅ ${bucket.name} (${bucket.binding})`);
            if (bucket.lifecycle?.enabled) {
                console.log(`      🔄 Lifecycle: ${bucket.lifecycle.rules?.length || 0} rules`);
            }
            if (bucket.cors) {
                console.log(`      🌐 CORS: ${bucket.cors.length} policies`);
            }
        });

        console.log(`   📊 Total buckets: ${buckets.length}`);
        console.log(`   📊 Unique names: ${bucketNames.size}`);
        console.log(`   📊 Unique bindings: ${bucketBindings.size}\n`);
    }

    /**
     * Validate Worker bindings consistency
     */
    validateWorkerBindings(config) {
        console.log('👷 Validating Worker Bindings...');

        if (!config.workers) {
            this.warnings.push('No workers defined in SOT');
            return;
        }

        const availableBuckets = new Set(config.r2?.buckets?.map(b => b.name) || []);
        const bucketBindings = new Map();

        // Create mapping of bucket names to their bindings
        config.r2?.buckets?.forEach(bucket => {
            bucketBindings.set(bucket.name, bucket.binding);
        });

        config.workers.forEach((worker, index) => {
            const workerId = `worker[${index}] (${worker.name})`;

            if (!worker.bindings?.r2) {
                console.log(`   ⚠️  ${workerId}: No R2 bindings defined`);
                return;
            }

            worker.bindings.r2.forEach((binding, bindingIndex) => {
                const bindingId = `${workerId}.r2[${bindingIndex}]`;

                if (!binding.bucket) {
                    this.errors.push(`${bindingId}: Missing bucket name`);
                    return;
                }

                if (!binding.binding) {
                    this.errors.push(`${bindingId}: Missing binding name`);
                    return;
                }

                // Check if bucket exists in SOT
                if (!availableBuckets.has(binding.bucket)) {
                    this.errors.push(`${bindingId}: References non-existent bucket '${binding.bucket}'`);
                }

                // Check binding consistency
                const expectedBinding = bucketBindings.get(binding.bucket);
                if (expectedBinding && expectedBinding !== binding.binding) {
                    this.warnings.push(`${bindingId}: Binding '${binding.binding}' differs from bucket's canonical binding '${expectedBinding}'`);
                }

                console.log(`   ✅ ${binding.bucket} → ${binding.binding}`);
            });
        });

        console.log('');
    }

    /**
     * Validate Control Plane specific configuration
     */
    validateControlPlaneConfig(config) {
        console.log('🎛️  Validating Control Plane Configuration...');

        if (!config.control_plane) {
            this.warnings.push('No control_plane configuration found');
            return;
        }

        const cp = config.control_plane;

        if (!cp.enabled) {
            console.log('   ⚠️  Control Plane is disabled');
            return;
        }

        // Validate monitoring configuration
        if (cp.monitoring?.enabled) {
            if (!cp.monitoring.metrics_bucket) {
                this.errors.push('Control Plane monitoring enabled but no metrics_bucket specified');
            } else {
                const bucketExists = config.r2?.buckets?.some(b => b.name === cp.monitoring.metrics_bucket);
                if (!bucketExists) {
                    this.errors.push(`Control Plane metrics_bucket '${cp.monitoring.metrics_bucket}' does not exist in R2 configuration`);
                }
            }
            console.log(`   📊 Monitoring: ${cp.monitoring.metrics_bucket} (${cp.monitoring.metrics_prefix || 'no prefix'})`);
        }

        // Validate backup configuration
        if (cp.backup?.enabled) {
            if (!cp.backup.destination_bucket) {
                this.errors.push('Control Plane backup enabled but no destination_bucket specified');
            } else {
                const bucketExists = config.r2?.buckets?.some(b => b.name === cp.backup.destination_bucket);
                if (!bucketExists) {
                    this.errors.push(`Control Plane destination_bucket '${cp.backup.destination_bucket}' does not exist in R2 configuration`);
                }
            }

            if (cp.backup.source_buckets) {
                cp.backup.source_buckets.forEach(bucketName => {
                    const bucketExists = config.r2?.buckets?.some(b => b.name === bucketName);
                    if (!bucketExists) {
                        this.errors.push(`Control Plane source_bucket '${bucketName}' does not exist in R2 configuration`);
                    }
                });
            }

            console.log(`   💾 Backup: ${cp.backup.source_buckets?.length || 0} sources → ${cp.backup.destination_bucket}`);
            console.log(`      Schedule: ${cp.backup.schedule || 'not specified'}`);
        }

        // Validate lifecycle management
        if (cp.lifecycle_management?.enabled) {
            console.log(`   🔄 Lifecycle Management: enabled (policy enforcement: ${cp.lifecycle_management.policy_enforcement || false})`);
        }

        console.log('');
    }

    /**
     * Verify Pulumi plan generation
     */
    async verifyPulumiPlan() {
        console.log('☁️  Verifying Pulumi Plan Generation...');

        try {
            // Check if Pulumi project exists
            const pulumiProjectPath = path.join(process.cwd(), 'pulumi', 'Pulumi.yaml');
            if (!fs.existsSync(pulumiProjectPath)) {
                this.warnings.push('Pulumi project not found, skipping plan verification');
                return;
            }

            // Run pulumi preview (dry-run)
            console.log('   🔄 Running Pulumi preview...');
            const stackName = `${this.environment}`;

            try {
                const output = execSync(`cd pulumi && pulumi preview --stack ${stackName} --non-interactive`,
                    { encoding: 'utf8', timeout: 30000 });

                console.log('   ✅ Pulumi preview completed successfully');

                // Analyze preview output for R2 resources
                const lines = output.split('\n');
                const r2Resources = lines.filter(line =>
                    line.includes('cloudflare:index/r2Bucket') ||
                    line.includes('r2Bucket') ||
                    line.includes('R2_')
                );

                if (r2Resources.length > 0) {
                    console.log(`   📊 R2 resources in plan: ${r2Resources.length}`);
                    r2Resources.forEach(resource => {
                        console.log(`      - ${resource.trim()}`);
                    });
                } else {
                    this.warnings.push('No R2 resources found in Pulumi plan');
                }

            } catch (error) {
                if (error.message.includes('stack not found')) {
                    this.warnings.push(`Pulumi stack '${stackName}' not found, skipping plan verification`);
                } else {
                    this.warnings.push(`Pulumi preview failed: ${error.message.split('\n')[0]}`);
                }
            }

        } catch (error) {
            this.warnings.push(`Failed to verify Pulumi plan: ${error.message}`);
        }

        console.log('');
    }

    /**
     * Verify wrangler.jsonc generation
     */
    verifyWranglerConfig() {
        console.log('⚙️  Verifying wrangler.jsonc Generation...');

        if (!fs.existsSync(this.wranglerConfigPath)) {
            this.warnings.push(`Generated wrangler.jsonc not found: ${this.wranglerConfigPath}`);
            console.log('   ⚠️  Generated wrangler.jsonc not found - run configuration generation first');
            return;
        }

        try {
            const content = fs.readFileSync(this.wranglerConfigPath, 'utf8');
            // Remove comments for JSON parsing
            const jsonContent = content.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
            const wranglerConfig = JSON.parse(jsonContent);

            console.log('   ✅ wrangler.jsonc loaded successfully');

            // Verify R2 bucket bindings
            if (wranglerConfig.r2_buckets) {
                console.log(`   🪣 R2 bucket bindings: ${wranglerConfig.r2_buckets.length}`);
                wranglerConfig.r2_buckets.forEach(bucket => {
                    console.log(`      - ${bucket.binding} → ${bucket.bucket_name}`);
                });
            } else {
                this.warnings.push('No R2 bucket bindings found in generated wrangler.jsonc');
            }

            // Verify KV bindings if present
            if (wranglerConfig.kv_namespaces) {
                console.log(`   🗂️  KV namespace bindings: ${wranglerConfig.kv_namespaces.length}`);
            }

            // Verify environment variables
            if (wranglerConfig.vars) {
                const envVarCount = Object.keys(wranglerConfig.vars).length;
                console.log(`   🔧 Environment variables: ${envVarCount}`);
            }

        } catch (error) {
            this.errors.push(`Failed to parse generated wrangler.jsonc: ${error.message}`);
        }

        console.log('');
    }

    /**
     * Perform comprehensive verification
     */
    async verify() {
        console.log('🚀 Starting R2 Control Plane Verification\n');

        // Load SOT configuration
        const config = this.loadSOTConfig();
        if (!config) {
            this.displayResults();
            return false;
        }

        // Perform validations
        this.validateR2Buckets(config);
        this.validateWorkerBindings(config);
        this.validateControlPlaneConfig(config);

        // Verify generated artifacts
        await this.verifyPulumiPlan();
        this.verifyWranglerConfig();

        // Display results
        this.displayResults();

        return this.errors.length === 0;
    }

    /**
     * Display verification results
     */
    displayResults() {
        console.log('📋 Verification Results');
        console.log('========================\n');

        if (this.errors.length === 0 && this.warnings.length === 0) {
            console.log('✅ All validations passed! R2 Control Plane configuration is consistent.\n');
            return;
        }

        if (this.errors.length > 0) {
            console.log('❌ Errors Found:');
            this.errors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error}`);
            });
            console.log('');
        }

        if (this.warnings.length > 0) {
            console.log('⚠️  Warnings:');
            this.warnings.forEach((warning, index) => {
                console.log(`   ${index + 1}. ${warning}`);
            });
            console.log('');
        }

        console.log(`Summary: ${this.errors.length} errors, ${this.warnings.length} warnings\n`);

        if (this.errors.length > 0) {
            console.log('🔧 Please fix the errors before proceeding with deployment.\n');
        }
    }
}

// CLI execution
async function main() {
    const environment = process.argv[2];

    if (!environment) {
        console.error('Usage: verify-r2-control-plane.js <environment>');
        console.error('Example: verify-r2-control-plane.js dev');
        process.exit(1);
    }

    const verifier = new R2ControlPlaneVerifier(environment);
    const success = await verifier.verify();

    process.exit(success ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(error => {
        console.error('Verification failed:', error);
        process.exit(1);
    });
}

export default R2ControlPlaneVerifier;