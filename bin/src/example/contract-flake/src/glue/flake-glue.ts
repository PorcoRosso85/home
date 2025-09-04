/**
 * Flake Glue Implementation
 * 
 * This module provides the core functionality for gluing Nix flakes together
 * based on their contract definitions.
 */

import {
  FlakeContract,
  FlakeContractBuilder,
  GlueConfiguration,
  GlueResult,
  GlueError,
  FlakeCapability,
  isFlakeContract,
  ContractValidator
} from '../types/flake-contract';

/**
 * Main Flake Glue class that orchestrates the composition of flakes
 */
export class FlakeGlue {
  private validator: FlakeContractValidator;

  constructor() {
    this.validator = new FlakeContractValidator();
  }

  /**
   * Glue multiple flakes together based on configuration
   */
  async glue(config: GlueConfiguration): Promise<GlueResult> {
    const errors: GlueError[] = [];
    const warnings: string[] = [];

    // Validate source contract
    if (!this.validator.validate(config.source)) {
      errors.push({
        type: 'constraint_violation',
        message: 'Invalid source contract',
        path: 'source'
      });
      return { success: false, errors };
    }

    // Validate target contracts
    for (let i = 0; i < config.targets.length; i++) {
      if (!this.validator.validate(config.targets[i])) {
        errors.push({
          type: 'constraint_violation',
          message: `Invalid target contract at index ${i}`,
          path: `targets[${i}]`
        });
      }
    }

    if (errors.length > 0) {
      return { success: false, errors };
    }

    // Check input/output compatibility
    for (const [targetInput, mapping] of Object.entries(config.mappings)) {
      const validationResult = this.validateMapping(
        targetInput,
        mapping,
        config.source,
        config.targets
      );
      
      if (!validationResult.valid) {
        errors.push(...validationResult.errors);
      }
      
      warnings.push(...validationResult.warnings);
    }

    if (errors.length > 0) {
      return { success: false, errors, warnings };
    }

    // Create composite contract
    const compositeContract = this.createCompositeContract(config);
    
    if (warnings.length > 0) {
      return {
        success: true,
        contract: compositeContract,
        warnings: warnings
      };
    }
    
    return {
      success: true,
      contract: compositeContract
    };
  }

  /**
   * Validate a single mapping between contracts
   */
  private validateMapping(
    targetInput: string,
    mapping: GlueConfiguration['mappings'][string],
    source: FlakeContract,
    targets: FlakeContract[]
  ): { valid: boolean; errors: GlueError[]; warnings: string[] } {
    const errors: GlueError[] = [];
    const warnings: string[] = [];

    // Check if the mapping source exists
    if (mapping.from === 'source' && mapping.output) {
      if (!(mapping.output in source.interface.outputs)) {
        errors.push({
          type: 'output_mismatch',
          message: `Source output '${mapping.output}' not found`,
          path: `mappings.${targetInput}`,
          expected: Object.keys(source.interface.outputs)
        });
      }
    }

    // Check capability requirements
    const requiredCapabilities = this.getRequiredCapabilities(targets);
    const missingCapabilities = requiredCapabilities.filter(
      cap => !source.capabilities.includes(cap)
    );

    if (missingCapabilities.length > 0) {
      warnings.push(
        `Source is missing capabilities: ${missingCapabilities.join(', ')}`
      );
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Create a composite contract from glue configuration
   */
  private createCompositeContract(config: GlueConfiguration): FlakeContract {
    const builder = new FlakeContractBuilder();
    
    // Set version as combination
    builder.version(`${config.source.version}-composite`);
    
    // Combine descriptions
    const descriptions = [
      config.source.description,
      ...config.targets.map(t => t.description)
    ].filter(Boolean);
    
    if (descriptions.length > 0) {
      builder.description(`Composite: ${descriptions.join(' + ')}`);
    }

    // Merge inputs
    for (const [name, input] of Object.entries(config.source.interface.inputs)) {
      builder.input(name, input);
    }
    
    for (const target of config.targets) {
      for (const [name, input] of Object.entries(target.interface.inputs)) {
        if (!config.mappings[name]) {
          builder.input(`target_${name}`, input);
        }
      }
    }

    // Merge outputs
    for (const [name, output] of Object.entries(config.source.interface.outputs)) {
      builder.output(name, output);
    }
    
    for (const target of config.targets) {
      for (const [name, output] of Object.entries(target.interface.outputs)) {
        builder.output(`target_${name}`, output);
      }
    }

    // Combine capabilities
    const allCapabilities = new Set<FlakeCapability>([
      ...config.source.capabilities,
      ...config.targets.flatMap(t => t.capabilities)
    ]);
    
    builder.capabilities(Array.from(allCapabilities));

    // Merge constraints
    const systems = new Set<string>();
    
    if (config.source.constraints?.systems) {
      config.source.constraints.systems.forEach(s => systems.add(s));
    }
    
    for (const target of config.targets) {
      if (target.constraints?.systems) {
        target.constraints.systems.forEach(s => systems.add(s));
      }
    }
    
    if (systems.size > 0) {
      builder.constraint('systems', Array.from(systems));
    }

    return builder.build();
  }

  /**
   * Get all required capabilities from targets
   */
  private getRequiredCapabilities(targets: FlakeContract[]): FlakeCapability[] {
    const capabilities = new Set<FlakeCapability>();
    
    for (const target of targets) {
      if (target.constraints?.requiredCapabilities) {
        target.constraints.requiredCapabilities.forEach(c => capabilities.add(c));
      }
    }
    
    return Array.from(capabilities);
  }

  /**
   * Check compatibility between two contracts
   */
  isCompatible(source: FlakeContract, target: FlakeContract): boolean {
    return this.validator.isCompatible(source, target);
  }
}

/**
 * Contract validator implementation
 */
class FlakeContractValidator implements ContractValidator {
  validate(contract: unknown): contract is FlakeContract {
    return isFlakeContract(contract);
  }

  validatePartial(contract: Partial<FlakeContract>): string[] {
    const errors: string[] = [];
    
    if (!contract.version) {
      errors.push('Version is required');
    }
    
    if (!contract.interface) {
      errors.push('Interface definition is required');
    } else {
      if (!contract.interface.inputs || typeof contract.interface.inputs !== 'object') {
        errors.push('Interface inputs must be an object');
      }
      if (!contract.interface.outputs || typeof contract.interface.outputs !== 'object') {
        errors.push('Interface outputs must be an object');
      }
    }
    
    if (!contract.capabilities || !Array.isArray(contract.capabilities)) {
      errors.push('Capabilities must be an array');
    }
    
    return errors;
  }

  isCompatible(source: FlakeContract, target: FlakeContract): boolean {
    // Check if source provides all required capabilities
    if (target.constraints?.requiredCapabilities) {
      const hasAll = target.constraints.requiredCapabilities.every(
        cap => source.capabilities.includes(cap)
      );
      if (!hasAll) return false;
    }

    // Check system compatibility
    if (source.constraints?.systems && target.constraints?.systems) {
      const targetSystems = target.constraints.systems;
      const intersection = source.constraints.systems.filter(
        s => targetSystems.includes(s)
      );
      if (intersection.length === 0) return false;
    }

    // Check if source outputs can satisfy target inputs
    for (const _inputName of Object.keys(target.interface.inputs)) {
      // This is a simplified check; real implementation would be more sophisticated
      const hasMatchingOutput = Object.keys(source.interface.outputs).some(
        _outputName => {
          // Could implement type checking here
          return true;
        }
      );
      
      if (!hasMatchingOutput) {
        return false;
      }
    }

    return true;
  }
}

// Example usage and CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('Flake Glue System v0.1.0');
  console.log('========================');
  console.log('');
  
  // Example: Create a sample contract
  const exampleContract = new FlakeContractBuilder()
    .version('1.0.0')
    .description('Example flake contract')
    .input('nixpkgs', 'flake:nixpkgs')
    .output('packages', { type: 'package' })
    .output('devShell', { type: 'devShell' })
    .capabilities(['bun', 'typescript', 'glue'])
    .build();
  
  console.log('Example Contract:');
  console.log(JSON.stringify(exampleContract, null, 2));
  
  // Demonstrate validation
  const validator = new FlakeContractValidator();
  
  if (validator.validate(exampleContract)) {
    console.log('\n✓ Contract is valid');
  } else {
    console.log('\n✗ Contract is invalid');
  }
  
  // Check for command line arguments
  const args = process.argv.slice(2);
  if (args.length > 0) {
    const command = args[0];
    
    switch (command) {
      case 'validate':
        if (args[1]) {
          // Validate a contract file
          console.log(`\nValidating contract file: ${args[1]}`);
          // Implementation would read and validate the file
        }
        break;
        
      case 'glue':
        if (args[1] && args[2]) {
          // Glue two contracts
          console.log(`\nGluing contracts: ${args[1]} + ${args[2]}`);
          // Implementation would read contracts and perform glue operation
        }
        break;
        
      default:
        console.log('\nAvailable commands:');
        console.log('  validate <file>    - Validate a contract file');
        console.log('  glue <src> <tgt>  - Glue two contracts together');
    }
  }
}

export default FlakeGlue;