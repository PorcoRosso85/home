# DQL Query Template System

A robust, type-safe TypeScript framework for creating parameterized, reusable database queries with comprehensive validation and documentation.

## Overview

This template system provides a foundation for creating 20 standardized query templates that address specific business pain points in partner revenue calculation and analysis. Each template is:

- **Type-safe** with full TypeScript support
- **Validated** with comprehensive parameter checking
- **Documented** with purpose, pain points, and examples
- **Reusable** across different contexts and applications
- **Maintainable** with clear separation of concerns

## Core Components

### 1. Type Definitions (`types.ts`)

Defines all interfaces and types used throughout the system:

- `QueryTemplate` - Main template interface
- `QueryParameter` - Parameter definition with validation rules
- `ValidationResult` - Validation feedback
- `TemplateRegistry` - Template management
- `TemplateExecutionResult` - Execution metadata

### 2. Base Template Class (`base.ts`)

Abstract base class providing:

- Parameter validation and type checking
- Error handling and meaningful feedback
- Helper methods for query generation
- Execution tracking and metadata

### 3. Template Registry (`index.ts`)

Complete template management system:

- Template registration and discovery
- Search by category, tag, or keyword
- Documentation generation
- Utility functions and helpers

## Quick Start

### Creating a Template

```typescript
import { BaseQueryTemplate, TemplateHelpers } from './index.js';

export class MyQueryTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'my_query',                    // Unique name
      'Solves specific problem',     // Purpose description
      'analytics',                   // Category
      [                             // Parameters
        TemplateHelpers.createParameter(
          'start_date',
          'date',
          'Analysis start date',
          { required: true }
        )
      ],
      {
        painPoint: 'Users struggle with complex date queries',
        tags: ['date', 'analytics']
      }
    );
  }

  protected generateQuery(params: Record<string, any>): string {
    return `MATCH (n) WHERE n.date >= date('${this.formatDate(params.start_date)}') RETURN n`;
  }
}
```

### Using a Template

```typescript
import { templateRegistry, PartnerRevenueTemplate } from './index.js';

// Register template
const template = new PartnerRevenueTemplate();
templateRegistry.register(template);

// Execute with parameters
const result = template.execute({
  revenue_start: '2024-01-01',
  revenue_end: '2024-01-31',
  min_revenue: 1000
});

if (result.validation.valid) {
  console.log('Generated query:', result.query);
} else {
  console.error('Validation errors:', result.validation.errors);
}
```

## Features

### Comprehensive Validation

- **Type checking** - Ensures parameters match expected types
- **Required parameters** - Validates all required parameters are provided
- **Custom rules** - Min/max values, regex patterns, custom functions
- **Meaningful errors** - Clear, actionable error messages

### Helper Utilities

- **Parameter creation** - `TemplateHelpers.createParameter()`
- **Date ranges** - `TemplateHelpers.createDateRange()`
- **Validation patterns** - Common regex patterns for IDs, dates, emails
- **String escaping** - Safe query generation helpers

### Discovery and Documentation

- **Search by category** - `registry.getByCategory('revenue')`
- **Search by tags** - `registry.getByTag('analytics')`
- **Keyword search** - `registry.search('partner')`
- **Auto-documentation** - `TemplateUtils.generateDocumentation(template)`

### Template Registry

```typescript
// Register templates
templateRegistry.register(new PartnerRevenueTemplate());
templateRegistry.register(new ChurnAnalysisTemplate());

// Discover templates
const revenueTemplates = templateRegistry.getByCategory('revenue');
const allCategories = templateRegistry.getCategories();
const searchResults = templateRegistry.search('partner');
```

## Parameter Types

| Type | Description | Validation |
|------|-------------|------------|
| `string` | Text values | Length, regex patterns |
| `number` | Integers | Min/max ranges |
| `decimal` | Floating point | Precision, ranges |
| `boolean` | True/false | Type checking |
| `date` | Date values | ISO format, parsing |
| `array` | Multiple values | Array validation |

## Validation Patterns

Pre-defined patterns for common validations:

```typescript
import { ValidationPatterns } from './index.js';

ValidationPatterns.EMAIL          // Email addresses
ValidationPatterns.UUID           // UUID format
ValidationPatterns.ISO_DATE       // YYYY-MM-DD
ValidationPatterns.PARTNER_ID     // PARTNER_XXXXXXXX
ValidationPatterns.DECIMAL_2      // Up to 2 decimal places
```

## Best Practices

### Template Design

1. **Single Responsibility** - Each template addresses one specific use case
2. **Clear Purpose** - Document the problem being solved
3. **Pain Point Focus** - Address specific user difficulties
4. **Comprehensive Parameters** - Include all necessary customization options
5. **Sensible Defaults** - Provide reasonable default values where appropriate

### Parameter Definition

1. **Descriptive Names** - Use clear, unambiguous parameter names
2. **Comprehensive Validation** - Include all necessary validation rules
3. **Example Values** - Provide realistic examples for documentation
4. **Required vs Optional** - Carefully consider what's truly required

### Query Generation

1. **SQL Injection Safe** - Always use provided escaping helpers
2. **Readable Output** - Generate well-formatted, readable queries
3. **Performance Aware** - Consider query performance implications
4. **Error Resilient** - Handle edge cases gracefully

## Architecture

```
templates/
├── types.ts           # Core type definitions
├── base.ts            # Abstract base class
├── index.ts           # Registry and utilities
├── example-template.ts # Example implementation
└── README.md          # This documentation
```

## Next Steps

This foundation supports the creation of 20 specific query templates addressing partner revenue calculation pain points. Each template will:

1. Extend `BaseQueryTemplate`
2. Define specific parameters and validation rules
3. Generate optimized Cypher/DQL queries
4. Include comprehensive documentation and examples
5. Address specific business pain points identified in requirements

The system is designed to be maintainable, extensible, and user-friendly, providing a solid foundation for complex query generation with type safety and comprehensive validation.