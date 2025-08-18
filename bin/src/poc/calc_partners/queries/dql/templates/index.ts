/**
 * DQL Query Template System - Main Export Module
 * 
 * This module serves as the main entry point for the DQL query template system.
 * It exports all core types, base classes, utilities, and provides a template registry.
 */

// Core type definitions
export type {
  ParameterType,
  ValidationRule,
  QueryParameter,
  QueryContext,
  ValidationResult,
  QueryTemplate,
  TemplateRegistry,
  TemplateExecutionResult,
  TemplateMetadata
} from './types.js';

// Base template class
export { BaseQueryTemplate } from './base.js';

// Template registry implementation
import {
  QueryTemplate,
  TemplateRegistry,
  TemplateMetadata
} from './types.js';

/**
 * Default implementation of the template registry
 */
export class DefaultTemplateRegistry implements TemplateRegistry {
  public readonly templates: Map<string, QueryTemplate> = new Map();

  /**
   * Register a new query template
   */
  public register(template: QueryTemplate): void {
    if (this.templates.has(template.name)) {
      throw new Error(`Template with name '${template.name}' is already registered`);
    }
    this.templates.set(template.name, template);
  }

  /**
   * Get template by name
   */
  public get(name: string): QueryTemplate | undefined {
    return this.templates.get(name);
  }

  /**
   * List all registered template names
   */
  public list(): string[] {
    return Array.from(this.templates.keys()).sort();
  }

  /**
   * Get templates by category
   */
  public getByCategory(category: string): QueryTemplate[] {
    return Array.from(this.templates.values())
      .filter(template => template.category === category)
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  /**
   * Get templates by tag
   */
  public getByTag(tag: string): QueryTemplate[] {
    return Array.from(this.templates.values())
      .filter(template => template.tags.includes(tag))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  /**
   * Search templates by keyword in name, purpose, or pain point
   */
  public search(keyword: string): QueryTemplate[] {
    const lowerKeyword = keyword.toLowerCase();
    return Array.from(this.templates.values())
      .filter(template => 
        template.name.toLowerCase().includes(lowerKeyword) ||
        template.purpose.toLowerCase().includes(lowerKeyword) ||
        (template.painPoint && template.painPoint.toLowerCase().includes(lowerKeyword)) ||
        template.tags.some(tag => tag.toLowerCase().includes(lowerKeyword))
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  /**
   * Get metadata for all templates
   */
  public getAllMetadata(): TemplateMetadata[] {
    return Array.from(this.templates.values())
      .map(template => ({
        name: template.name,
        purpose: template.purpose,
        category: template.category,
        tags: template.tags,
        parameterCount: template.parameters.length,
        requiredParameters: template.parameters.filter(p => p.required).map(p => p.name),
        painPoint: template.painPoint
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  /**
   * Get unique categories
   */
  public getCategories(): string[] {
    const categories = new Set<string>();
    for (const template of this.templates.values()) {
      categories.add(template.category);
    }
    return Array.from(categories).sort();
  }

  /**
   * Get unique tags
   */
  public getTags(): string[] {
    const tags = new Set<string>();
    for (const template of this.templates.values()) {
      template.tags.forEach(tag => tags.add(tag));
    }
    return Array.from(tags).sort();
  }

  /**
   * Clear all registered templates
   */
  public clear(): void {
    this.templates.clear();
  }

  /**
   * Check if a template is registered
   */
  public has(name: string): boolean {
    return this.templates.has(name);
  }

  /**
   * Remove a template
   */
  public remove(name: string): boolean {
    return this.templates.delete(name);
  }

  /**
   * Get template count
   */
  public count(): number {
    return this.templates.size;
  }
}

// Global registry instance
export const templateRegistry = new DefaultTemplateRegistry();

/**
 * Utility functions for template management
 */
export const TemplateUtils = {
  /**
   * Register multiple templates at once
   */
  registerAll(templates: QueryTemplate[], registry: TemplateRegistry = templateRegistry): void {
    for (const template of templates) {
      registry.register(template);
    }
  },

  /**
   * Validate template definition
   */
  validateTemplate(template: QueryTemplate): string[] {
    const errors: string[] = [];

    if (!template.name?.trim()) {
      errors.push('Template name is required');
    }

    if (!template.purpose?.trim()) {
      errors.push('Template purpose is required');
    }

    if (!template.category?.trim()) {
      errors.push('Template category is required');
    }

    if (!Array.isArray(template.parameters)) {
      errors.push('Template parameters must be an array');
    } else {
      // Validate parameter names are unique
      const paramNames = template.parameters.map(p => p.name);
      const uniqueNames = new Set(paramNames);
      if (paramNames.length !== uniqueNames.size) {
        errors.push('Parameter names must be unique');
      }

      // Validate each parameter
      template.parameters.forEach((param, index) => {
        if (!param.name?.trim()) {
          errors.push(`Parameter at index ${index} must have a name`);
        }
        if (!param.type) {
          errors.push(`Parameter '${param.name}' must have a type`);
        }
        if (typeof param.required !== 'boolean') {
          errors.push(`Parameter '${param.name}' must specify if it's required`);
        }
      });
    }

    if (typeof template.generate !== 'function') {
      errors.push('Template must have a generate function');
    }

    return errors;
  },

  /**
   * Create template documentation
   */
  generateDocumentation(template: QueryTemplate): string {
    const doc = [`# ${template.name}`, ''];
    
    doc.push(`**Purpose:** ${template.purpose}`);
    doc.push(`**Category:** ${template.category}`);
    
    if (template.painPoint) {
      doc.push(`**Pain Point:** ${template.painPoint}`);
    }
    
    if (template.tags.length > 0) {
      doc.push(`**Tags:** ${template.tags.join(', ')}`);
    }
    
    doc.push('', '## Parameters', '');
    
    if (template.parameters.length === 0) {
      doc.push('*No parameters required*');
    } else {
      template.parameters.forEach(param => {
        const required = param.required ? '**Required**' : 'Optional';
        doc.push(`### ${param.name} (${param.type}) - ${required}`);
        doc.push(`${param.description}`);
        
        if (param.default !== undefined) {
          doc.push(`*Default:* ${param.default}`);
        }
        
        if (param.examples && param.examples.length > 0) {
          doc.push(`*Examples:* ${param.examples.join(', ')}`);
        }
        
        doc.push('');
      });
    }

    if (template.examples && template.examples.length > 0) {
      doc.push('## Usage Examples', '');
      template.examples.forEach(example => {
        doc.push(`### ${example.name}`);
        doc.push(example.description);
        doc.push('```typescript');
        doc.push(`const params = ${JSON.stringify(example.parameters, null, 2)};`);
        doc.push('const query = template.generate(params);');
        doc.push('```');
        doc.push('');
      });
    }

    return doc.join('\n');
  }
};

// Export commonly used validation patterns
export const ValidationPatterns = {
  /** Email address pattern */
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  /** UUID pattern */
  UUID: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  /** ISO date pattern (YYYY-MM-DD) */
  ISO_DATE: /^\d{4}-\d{2}-\d{2}$/,
  /** ISO datetime pattern */
  ISO_DATETIME: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$/,
  /** Positive integer */
  POSITIVE_INTEGER: /^[1-9]\d*$/,
  /** Non-negative integer */
  NON_NEGATIVE_INTEGER: /^(0|[1-9]\d*)$/,
  /** Decimal with up to 2 places */
  DECIMAL_2: /^\d+(\.\d{1,2})?$/,
  /** Partner ID pattern */
  PARTNER_ID: /^PARTNER_[A-Z0-9]{8}$/,
  /** Product ID pattern */
  PRODUCT_ID: /^PROD_[A-Z0-9]{8}$/
};

// Export template creation helpers
export const TemplateHelpers = {
  /**
   * Create a parameter with common validation rules
   */
  createParameter: (
    name: string,
    type: ParameterType,
    description: string,
    options: {
      required?: boolean;
      default?: any;
      min?: number;
      max?: number;
      pattern?: RegExp;
      examples?: any[];
    } = {}
  ) => ({
    name,
    type,
    required: options.required ?? false,
    description,
    ...(options.default !== undefined && { default: options.default }),
    ...(options.examples && { examples: options.examples }),
    ...((options.min !== undefined || options.max !== undefined || options.pattern) && {
      validation: {
        ...(options.min !== undefined && { min: options.min }),
        ...(options.max !== undefined && { max: options.max }),
        ...(options.pattern && { pattern: options.pattern })
      }
    })
  }),

  /**
   * Create a date range parameter pair
   */
  createDateRange: (prefix: string = 'date') => [
    {
      name: `${prefix}_start`,
      type: 'date' as ParameterType,
      required: true,
      description: `Start date for ${prefix} range`,
      validation: {
        pattern: ValidationPatterns.ISO_DATE
      }
    },
    {
      name: `${prefix}_end`,
      type: 'date' as ParameterType,
      required: true,
      description: `End date for ${prefix} range`,
      validation: {
        pattern: ValidationPatterns.ISO_DATE
      }
    }
  ]
};

// Export all template instances
export { ltvCalculationTemplate } from './calculate-ltv.js';
export { partnerRewardTemplate } from './calculate-partner-reward.js';
export { revenueShareTemplate } from './calculate-revenue-share.js';
export { roiCalculationTemplate } from './calculate-roi.js';
export { tieredRateTemplate } from './calculate-tiered-rate.js';

// Export new aggregation and analysis templates
export { monthlyRevenueAggregationTemplate } from './aggregate-monthly-revenue.js';
export { partnerContributionAggregationTemplate } from './aggregate-partner-contribution.js';
export { cpaCalculationTemplate } from './calculate-cpa.js';
export { partnerPerformanceAnalysisTemplate } from './analyze-partner-performance.js';
export { revenueSensitivityAnalysisTemplate } from './analyze-revenue-sensitivity.js';
export { rewardStructureComparisonTemplate } from './compare-reward-structures.js';
export { productProfitabilityComparisonTemplate } from './compare-product-profitability.js';