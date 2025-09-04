/**
 * Minimal Glue Implementation
 * 
 * Ultra-thin glue layer that validates contracts and connects flakes.
 * The glue does minimal work - just validates and passes data through.
 */

import { 
  validateProviderOutput,
  validateProviderContract,
  type DataProviderContract,
  type DataProviderOutput 
} from '../contracts/data-provider.contract';
import { 
  validateConsumerInput,
  validateConsumerContract,
  validateOperationResult,
  ConsumerOperation,
  type DataConsumerContract,
  type ConsumerOutput
} from '../contracts/data-consumer.contract';

/**
 * Minimal glue configuration
 */
interface GlueConfig {
  providerContract: unknown;
  consumerContract: unknown;
  validateRuntime?: boolean;
}

/**
 * Glue result
 */
interface GlueResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * MinimalGlue class - thin orchestration layer
 */
export class MinimalGlue {
  private providerContract?: DataProviderContract;
  private consumerContract?: DataConsumerContract;
  private validateRuntime: boolean;

  constructor(config?: GlueConfig) {
    this.validateRuntime = config?.validateRuntime ?? true;
    
    if (config?.providerContract) {
      this.providerContract = validateProviderContract(config.providerContract);
    }
    
    if (config?.consumerContract) {
      this.consumerContract = validateConsumerContract(config.consumerContract);
    }
  }

  /**
   * Validate compatibility between provider and consumer
   */
  validateCompatibility(): GlueResult<boolean> {
    if (!this.providerContract || !this.consumerContract) {
      return {
        success: false,
        error: "Both provider and consumer contracts required"
      };
    }

    // Check if output format matches input format
    const providerFormat = this.providerContract.outputs.data.format;
    const consumerFormat = this.consumerContract.inputs.data.format;
    
    if (providerFormat !== consumerFormat) {
      return {
        success: false,
        error: `Format mismatch: provider outputs '${providerFormat}', consumer expects '${consumerFormat}'`
      };
    }

    // Check schema compatibility
    const providerSchema = this.providerContract.outputs.data.schema;
    const consumerSchema = this.consumerContract.inputs.data.schema;
    
    if (providerSchema !== consumerSchema) {
      return {
        success: false,
        error: `Schema mismatch: provider outputs '${providerSchema}', consumer expects '${consumerSchema}'`
      };
    }

    return { success: true, data: true };
  }

  /**
   * Pass data from provider to consumer with validation
   */
  async passThrough(
    providerData: unknown,
    operation: ConsumerOperation,
    processFunc: (data: DataProviderOutput) => Promise<unknown>
  ): Promise<GlueResult<ConsumerOutput>> {
    try {
      // Validate provider output
      const validatedInput = this.validateRuntime 
        ? validateProviderOutput(providerData)
        : providerData as DataProviderOutput;
      
      // Pass to consumer
      const result = await processFunc(validatedInput);
      
      // Validate consumer output
      const validatedOutput = this.validateRuntime
        ? validateOperationResult(operation, result)
        : result as ConsumerOutput;
      
      return { success: true, data: validatedOutput };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Direct connection - no transformation, just validation
   */
  connect(providerData: unknown): GlueResult<DataProviderOutput> {
    try {
      // Just validate and pass through
      const validated = validateConsumerInput(providerData);
      return { success: true, data: validated };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Validation failed'
      };
    }
  }
}

/**
 * Factory function for creating minimal glue instances
 */
export function createGlue(
  providerContract?: unknown,
  consumerContract?: unknown,
  validateRuntime = true
): MinimalGlue {
  return new MinimalGlue({
    providerContract,
    consumerContract,
    validateRuntime
  });
}

/**
 * Example usage / CLI entry
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('Minimal Glue System v0.1.0');
  console.log('========================\n');
  
  // Example contracts
  const exampleProviderContract: DataProviderContract = {
    version: "1.0.0",
    type: "data-provider",
    outputs: {
      data: {
        format: "json",
        schema: "products",
        path: "share/data/products.json"
      }
    },
    capabilities: ["data-source", "json", "static"]
  };
  
  const exampleConsumerContract: DataConsumerContract = {
    version: "1.0.0",
    type: "data-consumer",
    inputs: {
      data: {
        format: "json",
        schema: "products",
        required: true
      }
    },
    outputs: {
      summary: {
        format: "json",
        operations: ["summarize", "filter-category", "calculate-total"]
      }
    },
    capabilities: ["data-processor", "json", "jq"]
  };
  
  // Create glue instance
  const glue = createGlue(exampleProviderContract, exampleConsumerContract);
  
  // Check compatibility
  const compatibility = glue.validateCompatibility();
  
  if (compatibility.success) {
    console.log('✓ Contracts are compatible');
    
    // Example data
    const exampleData: DataProviderOutput = {
      products: [
        {
          id: "prod-001",
          name: "Widget A",
          price: 29.99,
          category: "hardware",
          metadata: { weight: 0.5, dimensions: [10, 10, 5] }
        }
      ],
      timestamp: new Date().toISOString(),
      version: "1.0.0"
    };
    
    // Test connection
    const connectionResult = glue.connect(exampleData);
    
    if (connectionResult.success) {
      console.log('✓ Data validation passed');
      console.log('\nValidated data structure:');
      console.log(JSON.stringify(connectionResult.data, null, 2));
    } else {
      console.log('✗ Data validation failed:', connectionResult.error);
    }
  } else {
    console.log('✗ Contracts incompatible:', compatibility.error);
  }
  
  // Show minimal nature
  console.log('\n📏 Glue metrics:');
  console.log('  - Lines of actual glue logic: ~50');
  console.log('  - Responsibilities: validation only');
  console.log('  - No data transformation');
  console.log('  - No business logic');
  console.log('  - Pure pass-through with contracts');
}

export default MinimalGlue;