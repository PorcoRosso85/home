/**
 * Contract Validator
 * 
 * Validates flake contracts and ensures compatibility.
 * Proof that flakes with contracts can connect successfully.
 */

import { 
  validateProviderOutput,
  validateProviderContract,
  type DataProviderContract,
  type DataProviderOutput 
} from './contracts/data-provider.contract';
import { 
  validateConsumerInput,
  validateConsumerContract,
  validateOperationResult,
  ConsumerOperation,
  type DataConsumerContract,
  type ConsumerOutput
} from './contracts/data-consumer.contract';

/**
 * Validator configuration
 */
interface ValidatorConfig {
  providerContract: unknown;
  consumerContract: unknown;
  validateRuntime?: boolean;
}

/**
 * Validation result
 */
interface ValidationResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * ContractValidator class - validates contract compatibility
 */
export class ContractValidator {
  private providerContract?: DataProviderContract;
  private consumerContract?: DataConsumerContract;
  private validateRuntime: boolean;

  constructor(config?: ValidatorConfig) {
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
  validateCompatibility(): ValidationResult<boolean> {
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
  ): Promise<ValidationResult<ConsumerOutput>> {
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
  connect(providerData: unknown): ValidationResult<DataProviderOutput> {
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
 * Factory function for creating validator instances
 */
export function createValidator(
  providerContract?: unknown,
  consumerContract?: unknown,
  validateRuntime = true
): ContractValidator {
  return new ContractValidator({
    providerContract,
    consumerContract,
    validateRuntime
  });
}

/**
 * Example usage / CLI entry
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('Contract Validator v1.0.0');
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
  
  // Create validator instance
  const validator = createValidator(exampleProviderContract, exampleConsumerContract);
  
  // Check compatibility
  const compatibility = validator.validateCompatibility();
  
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
    const connectionResult = validator.connect(exampleData);
    
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
  
  // Show validator nature
  console.log('\n✅ Validator metrics:');
  console.log('  - Core responsibility: contract validation');
  console.log('  - No data transformation');
  console.log('  - No business logic');
  console.log('  - Proof that contracts enable connection');
}

export default ContractValidator;