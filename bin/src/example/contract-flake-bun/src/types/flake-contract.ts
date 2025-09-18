/**
 * Flake Contract Type Definitions
 * 
 * This module defines TypeScript types that represent Nix flake contracts,
 * enabling type-safe composition and validation of flake systems.
 */

// Core primitive types for Nix values
export type NixValue = 
  | string 
  | number 
  | boolean 
  | null 
  | NixAttrSet 
  | NixList 
  | NixFunction
  | NixDerivation;

export interface NixAttrSet {
  [key: string]: NixValue;
}

export type NixList = NixValue[];

export interface NixFunction {
  __type: 'function';
  params: string[];
  body?: unknown;
}

export interface NixDerivation {
  __type: 'derivation';
  name: string;
  system: string;
  builder: string;
  args?: string[];
  outputs?: string[];
}

// Flake-specific types
export interface FlakeRef {
  type: 'github' | 'git' | 'path' | 'flake';
  url: string;
  ref?: string;
  rev?: string;
}

export interface FlakeInput {
  url: string | FlakeRef;
  follows?: string;
  flake?: boolean;
}

export interface FlakeOutput {
  type: 'package' | 'devShell' | 'app' | 'overlay' | 'nixosModule' | 'contract' | 'lib';
  schema?: unknown;
}

// Capability system for flakes
export type FlakeCapability = 
  | 'bun'
  | 'deno'
  | 'node'
  | 'python'
  | 'rust'
  | 'go'
  | 'nix'
  | 'typescript'
  | 'glue'
  | 'test'
  | 'build'
  | 'deploy';

// Main contract interface
export interface FlakeContract {
  version: string;
  description?: string;
  
  interface: {
    inputs: Record<string, FlakeInput | string>;
    outputs: Record<string, FlakeOutput | string>;
  };
  
  capabilities: FlakeCapability[];
  
  // Constraints and requirements
  constraints?: {
    systems?: string[];
    nixVersion?: string;
    requiredCapabilities?: FlakeCapability[];
  };
  
  // Metadata
  metadata?: {
    author?: string;
    license?: string;
    homepage?: string;
    documentation?: string;
  };
}

// Glue-specific types
export interface GlueConfiguration {
  source: FlakeContract;
  targets: FlakeContract[];
  
  mappings: {
    [targetInput: string]: {
      from: 'source' | 'target' | 'external';
      output?: string;
      transform?: (value: NixValue) => NixValue;
    };
  };
  
  validation?: {
    strict: boolean;
    allowUnknownOutputs?: boolean;
    requireAllCapabilities?: boolean;
  };
}

export interface GlueResult {
  success: boolean;
  contract?: FlakeContract;
  errors?: GlueError[];
  warnings?: string[];
}

export interface GlueError {
  type: 'input_missing' | 'output_mismatch' | 'capability_missing' | 'constraint_violation';
  message: string;
  path?: string;
  expected?: unknown;
  actual?: unknown;
}

// Validation utilities
export interface ContractValidator {
  validate(contract: unknown): contract is FlakeContract;
  validatePartial(contract: Partial<FlakeContract>): string[];
  isCompatible(source: FlakeContract, target: FlakeContract): boolean;
}

// Type guards
export function isNixDerivation(value: NixValue): value is NixDerivation {
  return typeof value === 'object' && 
    value !== null && 
    '__type' in value && 
    value.__type === 'derivation';
}

export function isNixFunction(value: NixValue): value is NixFunction {
  return typeof value === 'object' && 
    value !== null && 
    '__type' in value && 
    value.__type === 'function';
}

export function isFlakeContract(value: unknown): value is FlakeContract {
  if (typeof value !== 'object' || value === null) return false;
  
  const contract = value as any;
  return typeof contract.version === 'string' &&
    typeof contract.interface === 'object' &&
    Array.isArray(contract.capabilities);
}

// Contract builder for fluent API
export class FlakeContractBuilder {
  private contract: Partial<FlakeContract> = {
    interface: { inputs: {}, outputs: {} },
    capabilities: []
  };

  version(v: string): this {
    this.contract.version = v;
    return this;
  }

  description(d: string): this {
    this.contract.description = d;
    return this;
  }

  input(name: string, input: FlakeInput | string): this {
    this.contract.interface!.inputs[name] = input;
    return this;
  }

  output(name: string, output: FlakeOutput | string): this {
    this.contract.interface!.outputs[name] = output;
    return this;
  }

  capability(cap: FlakeCapability): this {
    this.contract.capabilities!.push(cap);
    return this;
  }

  capabilities(caps: FlakeCapability[]): this {
    this.contract.capabilities!.push(...caps);
    return this;
  }

  constraint(key: keyof NonNullable<FlakeContract['constraints']>, value: any): this {
    if (!this.contract.constraints) {
      this.contract.constraints = {};
    }
    (this.contract.constraints as any)[key] = value;
    return this;
  }

  build(): FlakeContract {
    if (!this.contract.version) {
      throw new Error('Contract version is required');
    }
    return this.contract as FlakeContract;
  }
}