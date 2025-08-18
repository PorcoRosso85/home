/**
 * DQL Query Template System - Type Definitions
 * 
 * This module defines the core interfaces and types for the DQL query template system.
 * It provides a robust foundation for creating parameterized, reusable database queries.
 */

/**
 * Supported parameter types for query templates
 */
export type ParameterType = 'string' | 'number' | 'date' | 'boolean' | 'decimal' | 'array';

/**
 * Validation rule for query parameters
 */
export interface ValidationRule {
  /** Minimum value for numbers/decimals, minimum length for strings */
  min?: number;
  /** Maximum value for numbers/decimals, maximum length for strings */
  max?: number;
  /** Regular expression pattern for string validation */
  pattern?: RegExp;
  /** Custom validation function */
  custom?: (value: any) => boolean | string;
}

/**
 * Definition of a query parameter
 */
export interface QueryParameter {
  /** Parameter name used in the query template */
  name: string;
  /** Data type of the parameter */
  type: ParameterType;
  /** Whether this parameter is required */
  required: boolean;
  /** Default value if parameter is not provided */
  default?: any;
  /** Human-readable description of the parameter */
  description: string;
  /** Validation rules for the parameter */
  validation?: ValidationRule;
  /** Example values for documentation */
  examples?: any[];
}

/**
 * Context information for query execution
 */
export interface QueryContext {
  /** User or system executing the query */
  executor?: string;
  /** Timestamp of query execution */
  timestamp?: Date;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Result of parameter validation
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean;
  /** Error messages if validation failed */
  errors: string[];
  /** Warnings that don't prevent execution */
  warnings: string[];
}

/**
 * Main query template interface
 */
export interface QueryTemplate {
  /** Unique identifier for the template */
  name: string;
  /** Human-readable purpose description */
  purpose: string;
  /** Business pain point this query addresses */
  painPoint?: string;
  /** Category/domain of the query (e.g., 'revenue', 'partner', 'analytics') */
  category: string;
  /** Array of parameters this template accepts */
  parameters: QueryParameter[];
  /** Tags for categorization and search */
  tags: string[];
  /** 
   * Generate the actual query string from parameters
   * @param params - Parameter values
   * @param context - Execution context
   * @returns Generated DQL/Cypher query string
   */
  generate: (params: Record<string, any>, context?: QueryContext) => string;
  /**
   * Validate parameters before query generation
   * @param params - Parameter values to validate
   * @returns Validation result
   */
  validate?: (params: Record<string, any>) => ValidationResult;
  /** Example usage scenarios */
  examples?: Array<{
    name: string;
    description: string;
    parameters: Record<string, any>;
    expectedResult?: string;
  }>;
}

/**
 * Template registry for managing multiple query templates
 */
export interface TemplateRegistry {
  /** All registered templates */
  templates: Map<string, QueryTemplate>;
  /** Register a new template */
  register: (template: QueryTemplate) => void;
  /** Get template by name */
  get: (name: string) => QueryTemplate | undefined;
  /** List all template names */
  list: () => string[];
  /** Find templates by category */
  getByCategory: (category: string) => QueryTemplate[];
  /** Find templates by tag */
  getByTag: (tag: string) => QueryTemplate[];
  /** Search templates by keyword */
  search: (keyword: string) => QueryTemplate[];
}

/**
 * Template execution result
 */
export interface TemplateExecutionResult {
  /** Generated query string */
  query: string;
  /** Parameters used */
  parameters: Record<string, any>;
  /** Execution context */
  context?: QueryContext;
  /** Validation result */
  validation: ValidationResult;
  /** Execution timestamp */
  timestamp: Date;
}

/**
 * Template metadata for documentation and discovery
 */
export interface TemplateMetadata {
  /** Template name */
  name: string;
  /** Purpose description */
  purpose: string;
  /** Category */
  category: string;
  /** Tags */
  tags: string[];
  /** Number of parameters */
  parameterCount: number;
  /** Required parameters */
  requiredParameters: string[];
  /** Pain point addressed */
  painPoint?: string;
}