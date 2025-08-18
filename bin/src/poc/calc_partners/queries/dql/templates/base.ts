/**
 * DQL Query Template System - Base Template Class
 * 
 * This module provides the base implementation for query templates with
 * comprehensive validation, parameter processing, and error handling.
 */

import {
  QueryTemplate,
  QueryParameter,
  QueryContext,
  ValidationResult,
  ValidationRule,
  ParameterType,
  TemplateExecutionResult,
  TemplateMetadata
} from './types.js';

/**
 * Base abstract class for all query templates
 */
export abstract class BaseQueryTemplate implements QueryTemplate {
  public readonly name: string;
  public readonly purpose: string;
  public readonly painPoint?: string;
  public readonly category: string;
  public readonly parameters: QueryParameter[];
  public readonly tags: string[];

  constructor(
    name: string,
    purpose: string,
    category: string,
    parameters: QueryParameter[],
    options: {
      painPoint?: string;
      tags?: string[];
    } = {}
  ) {
    this.name = name;
    this.purpose = purpose;
    this.category = category;
    this.parameters = parameters;
    this.painPoint = options.painPoint;
    this.tags = options.tags || [];

    // Validate template definition at construction
    this.validateTemplateDefinition();
  }

  /**
   * Abstract method to be implemented by concrete templates
   * Generates the actual query string
   */
  public abstract generateQuery(params: Record<string, any>, context?: QueryContext): string;

  /**
   * Main entry point for query generation
   */
  public generate(params: Record<string, any>, context?: QueryContext): string {
    const validation = this.validate(params);
    if (!validation.valid) {
      throw new Error(`Parameter validation failed: ${validation.errors.join(', ')}`);
    }

    // Process parameters (apply defaults, type conversion)
    const processedParams = this.processParameters(params);
    
    return this.generateQuery(processedParams, context);
  }

  /**
   * Comprehensive parameter validation
   */
  public validate(params: Record<string, any>): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    for (const param of this.parameters) {
      const value = params[param.name];

      // Check required parameters
      if (param.required && (value === undefined || value === null)) {
        errors.push(`Required parameter '${param.name}' is missing`);
        continue;
      }

      // Skip validation for optional parameters that are not provided
      if (!param.required && (value === undefined || value === null)) {
        continue;
      }

      // Type validation
      const typeValidation = this.validateParameterType(param, value);
      if (!typeValidation.valid) {
        errors.push(...typeValidation.errors);
      }

      // Custom validation rules
      if (param.validation) {
        const ruleValidation = this.validateParameterRules(param, value);
        if (!ruleValidation.valid) {
          errors.push(...ruleValidation.errors);
        }
        warnings.push(...ruleValidation.warnings);
      }
    }

    // Check for unexpected parameters
    const expectedParams = new Set(this.parameters.map(p => p.name));
    const providedParams = new Set(Object.keys(params));
    const unexpectedParams = Array.from(providedParams).filter(p => !expectedParams.has(p));
    
    if (unexpectedParams.length > 0) {
      warnings.push(`Unexpected parameters provided: ${unexpectedParams.join(', ')}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Execute template with full result metadata
   */
  public execute(params: Record<string, any>, context?: QueryContext): TemplateExecutionResult {
    const validation = this.validate(params);
    const timestamp = new Date();
    const processedParams = this.processParameters(params);

    let query = '';
    if (validation.valid) {
      query = this.generateQuery(processedParams, context);
    }

    return {
      query,
      parameters: processedParams,
      context,
      validation,
      timestamp
    };
  }

  /**
   * Get template metadata for discovery and documentation
   */
  public getMetadata(): TemplateMetadata {
    return {
      name: this.name,
      purpose: this.purpose,
      category: this.category,
      tags: this.tags,
      parameterCount: this.parameters.length,
      requiredParameters: this.parameters.filter(p => p.required).map(p => p.name),
      painPoint: this.painPoint
    };
  }

  /**
   * Process parameters: apply defaults and type conversion
   */
  private processParameters(params: Record<string, any>): Record<string, any> {
    const processed: Record<string, any> = { ...params };

    for (const param of this.parameters) {
      const value = params[param.name];

      // Apply default values
      if ((value === undefined || value === null) && param.default !== undefined) {
        processed[param.name] = param.default;
        continue;
      }

      // Type conversion
      if (value !== undefined && value !== null) {
        processed[param.name] = this.convertParameterType(param.type, value);
      }
    }

    return processed;
  }

  /**
   * Validate parameter type
   */
  private validateParameterType(param: QueryParameter, value: any): ValidationResult {
    const errors: string[] = [];

    switch (param.type) {
      case 'string':
        if (typeof value !== 'string') {
          errors.push(`Parameter '${param.name}' must be a string`);
        }
        break;
      case 'number':
        if (typeof value !== 'number' || isNaN(value)) {
          errors.push(`Parameter '${param.name}' must be a valid number`);
        }
        break;
      case 'decimal':
        if (typeof value !== 'number' || isNaN(value)) {
          errors.push(`Parameter '${param.name}' must be a valid decimal number`);
        }
        break;
      case 'boolean':
        if (typeof value !== 'boolean') {
          errors.push(`Parameter '${param.name}' must be a boolean`);
        }
        break;
      case 'date':
        if (!(value instanceof Date) && typeof value !== 'string') {
          errors.push(`Parameter '${param.name}' must be a Date or date string`);
        } else if (typeof value === 'string' && isNaN(Date.parse(value))) {
          errors.push(`Parameter '${param.name}' must be a valid date string`);
        }
        break;
      case 'array':
        if (!Array.isArray(value)) {
          errors.push(`Parameter '${param.name}' must be an array`);
        }
        break;
      default:
        errors.push(`Unknown parameter type '${param.type}' for parameter '${param.name}'`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings: []
    };
  }

  /**
   * Validate parameter against custom rules
   */
  private validateParameterRules(param: QueryParameter, value: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const rules = param.validation!;

    // Min/Max validation
    if (rules.min !== undefined) {
      if (param.type === 'string' && typeof value === 'string') {
        if (value.length < rules.min) {
          errors.push(`Parameter '${param.name}' must be at least ${rules.min} characters long`);
        }
      } else if ((param.type === 'number' || param.type === 'decimal') && typeof value === 'number') {
        if (value < rules.min) {
          errors.push(`Parameter '${param.name}' must be at least ${rules.min}`);
        }
      }
    }

    if (rules.max !== undefined) {
      if (param.type === 'string' && typeof value === 'string') {
        if (value.length > rules.max) {
          errors.push(`Parameter '${param.name}' must be at most ${rules.max} characters long`);
        }
      } else if ((param.type === 'number' || param.type === 'decimal') && typeof value === 'number') {
        if (value > rules.max) {
          errors.push(`Parameter '${param.name}' must be at most ${rules.max}`);
        }
      }
    }

    // Pattern validation for strings
    if (rules.pattern && param.type === 'string' && typeof value === 'string') {
      if (!rules.pattern.test(value)) {
        errors.push(`Parameter '${param.name}' does not match required pattern`);
      }
    }

    // Custom validation function
    if (rules.custom) {
      const result = rules.custom(value);
      if (typeof result === 'string') {
        errors.push(result);
      } else if (!result) {
        errors.push(`Parameter '${param.name}' failed custom validation`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Convert value to the expected parameter type
   */
  private convertParameterType(type: ParameterType, value: any): any {
    switch (type) {
      case 'string':
        return String(value);
      case 'number':
      case 'decimal':
        return typeof value === 'number' ? value : Number(value);
      case 'boolean':
        return typeof value === 'boolean' ? value : Boolean(value);
      case 'date':
        return value instanceof Date ? value : new Date(value);
      case 'array':
        return Array.isArray(value) ? value : [value];
      default:
        return value;
    }
  }

  /**
   * Validate template definition at construction time
   */
  private validateTemplateDefinition(): void {
    if (!this.name || typeof this.name !== 'string') {
      throw new Error('Template name must be a non-empty string');
    }

    if (!this.purpose || typeof this.purpose !== 'string') {
      throw new Error('Template purpose must be a non-empty string');
    }

    if (!this.category || typeof this.category !== 'string') {
      throw new Error('Template category must be a non-empty string');
    }

    if (!Array.isArray(this.parameters)) {
      throw new Error('Template parameters must be an array');
    }

    // Check for duplicate parameter names
    const paramNames = this.parameters.map(p => p.name);
    const uniqueNames = new Set(paramNames);
    if (paramNames.length !== uniqueNames.size) {
      throw new Error('Template parameters must have unique names');
    }

    // Validate each parameter definition
    for (const param of this.parameters) {
      if (!param.name || typeof param.name !== 'string') {
        throw new Error('Parameter name must be a non-empty string');
      }
      if (!param.type) {
        throw new Error(`Parameter '${param.name}' must have a valid type`);
      }
      if (typeof param.required !== 'boolean') {
        throw new Error(`Parameter '${param.name}' required flag must be boolean`);
      }
    }
  }

  /**
   * Helper method to escape string values for Cypher queries
   */
  protected escapeString(value: string): string {
    return value.replace(/'/g, "\\'").replace(/"/g, '\\"');
  }

  /**
   * Helper method to format date values for Cypher queries
   */
  protected formatDate(date: Date | string): string {
    const d = date instanceof Date ? date : new Date(date);
    return d.toISOString().split('T')[0]; // YYYY-MM-DD format
  }

  /**
   * Helper method to format datetime values for Cypher queries
   */
  protected formatDateTime(date: Date | string): string {
    const d = date instanceof Date ? date : new Date(date);
    return d.toISOString();
  }
}