// Type definitions for Contract Service POC

// Result type pattern for error handling
export type Result<T, E> = 
  | { ok: true; data: T }
  | { ok: false; error: E };

// Specific error types
export type RegistryError = {
  type: 'SCHEMA_FILE_NOT_FOUND' | 'INVALID_JSON' | 'INVALID_SCHEMA' | 'MISSING_PARAMETER' | 'INVALID_PARAMETER_TYPE';
  message: string;
  details?: unknown;
};

export type RouterError = {
  type: 'NO_PROVIDER_FOUND' | 'PROVIDER_CALL_FAILED' | 'TRANSFORM_FAILED';
  message: string;
  details?: unknown;
};

export type TransformerError = {
  type: 'NO_TRANSFORM_AVAILABLE' | 'TRANSFORM_EXECUTION_ERROR';
  message: string;
};

// Schema types
export interface JsonSchema {
  type?: string;
  properties?: Record<string, unknown>;
  required?: string[];
  $ref?: string;
  allOf?: unknown[];
  anyOf?: unknown[];
  oneOf?: unknown[];
}

// Registration types
export interface ProviderRegistration {
  uri: string;
  inputSchemaPath: string;
  outputSchemaPath: string;
  endpoint?: string;
  metadata?: any;
}

export interface ConsumerRegistration {
  uri: string;
  expectsInputSchemaPath: string;
  expectsOutputSchemaPath: string;
}

// Schema data types
export interface SchemaData {
  input: JsonSchema;
  output: JsonSchema;
}