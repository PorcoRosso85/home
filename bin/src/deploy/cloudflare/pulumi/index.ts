import * as pulumi from "@pulumi/pulumi";
import * as cloudflare from "@pulumi/cloudflare";
import * as path from "path";

// Import SOT helper
const sopsYaml = require("../helpers/sops-yaml.js");

/**
 * Cloudflare Deployment Management using Pulumi TypeScript
 *
 * This module implements SOT (Single Source of Truth) direct reading to dynamically
 * generate Pulumi resources for Cloudflare R2 buckets and Workers based on
 * environment-specific configuration files.
 */

// Get stack name from environment variable or pulumi stack name
const stack = pulumi.getStack();
const environment = process.env.ENVIRONMENT || stack;

// Validate environment
if (!environment || !['dev', 'stg', 'prod'].includes(environment)) {
    throw new Error(`Invalid environment: ${environment}. Must be one of: dev, stg, prod`);
}

console.log(`🎯 Deploying to environment: ${environment}`);

// Get Pulumi configuration
const config = new pulumi.Config();
const cfAccountId = config.requireSecret("cf:accountId");
const cfApiToken = config.requireSecret("cf:apiToken");

// Configure Cloudflare provider
const provider = new cloudflare.Provider("cloudflare", {
    apiToken: cfApiToken,
});

// SOT Configuration Loading
let sotConfig: any;
const r2Buckets: cloudflare.R2Bucket[] = [];
const workerScripts: cloudflare.WorkerScript[] = [];

/**
 * Load SOT configuration and create resources dynamically
 */
async function loadSOTAndCreateResources() {
    try {
        console.log(`📋 Loading SOT configuration for ${environment} environment...`);

        // Load SOT configuration using the helper
        sotConfig = await sopsYaml.getSOTConfig(environment, {
            skipValidation: false,  // Enable JSON Schema validation
            cacheTTL: 60000        // Cache for 1 minute
        });

        console.log(`✅ SOT configuration loaded successfully`);
        console.log(`📊 Configuration version: ${sotConfig.version}`);

        // Create R2 buckets from SOT
        if (sotConfig.r2 && sotConfig.r2.buckets) {
            console.log(`🪣 Creating ${sotConfig.r2.buckets.length} R2 buckets...`);

            for (const bucketConfig of sotConfig.r2.buckets) {
                const bucketName = bucketConfig.name;
                const bucketBinding = bucketConfig.binding;

                if (!bucketName || !bucketBinding) {
                    throw new Error(`Invalid R2 bucket configuration: missing name or binding`);
                }

                console.log(`  🪣 Creating bucket: ${bucketName} (binding: ${bucketBinding})`);

                const bucket = new cloudflare.R2Bucket(`r2-${bucketName}`, {
                    accountId: cfAccountId,
                    name: bucketName,
                    location: "WNAM"  // Default to Western North America
                }, {
                    provider,
                    protect: environment === 'prod'  // Protect production buckets from deletion
                });

                r2Buckets.push(bucket);
            }
        } else {
            console.log(`ℹ️  No R2 buckets configured in SOT`);
        }

        // Create Workers from SOT
        if (sotConfig.workers && Array.isArray(sotConfig.workers)) {
            console.log(`⚙️  Creating ${sotConfig.workers.length} Worker scripts...`);

            for (const workerConfig of sotConfig.workers) {
                const workerName = workerConfig.name;
                const scriptPath = workerConfig.script;

                if (!workerName) {
                    throw new Error(`Invalid Worker configuration: missing name`);
                }

                console.log(`  ⚙️  Creating worker: ${workerName}`);

                // Create basic worker configuration
                // Note: In a real deployment, you'd want to read the actual script content
                const worker = new cloudflare.WorkerScript(`worker-${workerName}`, {
                    accountId: cfAccountId,
                    name: workerName,
                    content: `// Placeholder for ${workerName}\nexport default { fetch() { return new Response('Hello from ${workerName}'); } }`,

                    // Configure R2 bindings if specified
                    r2BucketBindings: workerConfig.bindings?.r2?.map((binding: any) => ({
                        name: binding.binding,
                        bucketName: binding.bucket
                    })) || []
                }, {
                    provider,
                    protect: environment === 'prod'  // Protect production workers from deletion
                });

                workerScripts.push(worker);
            }
        } else {
            console.log(`ℹ️  No Workers configured in SOT`);
        }

    } catch (error) {
        console.error(`❌ Failed to load SOT configuration:`, error);
        throw error;
    }
}

// Load SOT configuration and create resources
// Note: This is a top-level await, which requires Node.js 14+ and proper TypeScript configuration
loadSOTAndCreateResources().catch(error => {
    console.error(`❌ Deployment failed:`, error.message);
    process.exit(1);
});

// Export configuration for verification
export const deploymentInfo = pulumi.output({
    environment,
    timestamp: new Date().toISOString(),
    sotVersion: sotConfig?.version || 'unknown',
    resourceCounts: {
        r2Buckets: r2Buckets.length,
        workers: workerScripts.length
    }
});

// Export R2 bucket names
export const r2BucketNames = pulumi.output(r2Buckets.map(bucket => bucket.name));

// Export Worker names
export const workerNames = pulumi.output(workerScripts.map(worker => worker.name));

// Export account configuration
export const accountId = cfAccountId;