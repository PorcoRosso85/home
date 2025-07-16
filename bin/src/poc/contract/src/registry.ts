// Contract Registry - Manages provider and consumer registrations
import { Database } from "./kuzu_wrapper.ts";
import { log } from "../../../log/mod.ts";
import type { 
  Result, 
  RegistryError, 
  ProviderRegistration, 
  ConsumerRegistration,
  SchemaData,
  JsonSchema
} from "./types.ts";

export class Registry {
  constructor(private db: Database) {}
  
  async registerProvider(data: ProviderRegistration): Promise<Result<{ status: string; provider: string; schema: SchemaData }, RegistryError>> {
    // Read and validate schema files
    const schemaResult = await this.loadSchemaFromPaths(
      data.inputSchemaPath,
      data.outputSchemaPath
    );
    
    if (!schemaResult.ok) {
      return schemaResult;
    }

    const schema = schemaResult.data;
    
    try {
      // Store in graph DB
      await this.db.query(`
        MERGE (p:Provider {uri: $uri})
        SET p.endpoint = $endpoint,
            p.metadata = $metadata
        WITH p
        MERGE (s:Schema {
          input: $input,
          output: $output,
          hash: $hash
        })
        MERGE (p)-[:PROVIDES]->(s)
      `, {
        uri: data.uri,
        endpoint: data.endpoint || null,
        metadata: JSON.stringify(data.metadata || {}),
        input: JSON.stringify(schema.input),
        output: JSON.stringify(schema.output),
        hash: this.hashSchema(schema)
      });
      
      log("INFO", {
        uri: "contract.registry.registerProvider",
        message: "Provider registered successfully",
        providerUri: data.uri
      });

      return {
        ok: true,
        data: {
          status: "registered",
          provider: data.uri,
          schema // Return loaded schema for confirmation
        }
      };
    } catch (error) {
      log("ERROR", {
        uri: "contract.registry.registerProvider",
        message: "Failed to store provider in database",
        error: error instanceof Error ? error.message : String(error),
        providerUri: data.uri
      });
      
      return {
        ok: false,
        error: {
          type: 'INVALID_SCHEMA',
          message: "Failed to register provider",
          details: error
        }
      };
    }
  }
  
  async registerConsumer(data: ConsumerRegistration): Promise<Result<{ status: string; consumer: string; expects: SchemaData }, RegistryError>> {
    // Read and validate schema files
    const schemaResult = await this.loadSchemaFromPaths(
      data.expectsInputSchemaPath,
      data.expectsOutputSchemaPath
    );
    
    if (!schemaResult.ok) {
      return schemaResult;
    }

    const expects = schemaResult.data;
    
    try {
      // Store in graph DB
      await this.db.query(`
        MERGE (c:Consumer {uri: $uri})
        WITH c
        MERGE (s:Schema {
          input: $input,
          output: $output,
          hash: $hash
        })
        MERGE (c)-[:EXPECTS]->(s)
      `, {
        uri: data.uri,
        input: JSON.stringify(expects.input),
        output: JSON.stringify(expects.output),
        hash: this.hashSchema(expects)
      });
      
      // Trigger matching for new consumer
      await this.findAndCreateMatches(data.uri);
      
      log("INFO", {
        uri: "contract.registry.registerConsumer",
        message: "Consumer registered successfully",
        consumerUri: data.uri
      });

      return {
        ok: true,
        data: {
          status: "registered",
          consumer: data.uri,
          expects // Return loaded schema for confirmation
        }
      };
    } catch (error) {
      log("ERROR", {
        uri: "contract.registry.registerConsumer",
        message: "Failed to store consumer in database",
        error: error instanceof Error ? error.message : String(error),
        consumerUri: data.uri
      });
      
      return {
        ok: false,
        error: {
          type: 'INVALID_SCHEMA',
          message: "Failed to register consumer",
          details: error
        }
      };
    }
  }
  
  private async findAndCreateMatches(consumerUri: string) {
    // Find compatible providers - simplified for MVP
    // In real implementation, match based on schema compatibility
    const result = await this.db.query(`
      MATCH (c:Consumer {uri: $uri})
      MATCH (p:Provider)
      MERGE (c)-[r:CAN_CALL]->(p)
      SET r.transform = $defaultTransform
      RETURN p.uri as provider
    `, {
      uri: consumerUri,
      defaultTransform: JSON.stringify(this.generateDefaultTransform())
    });
    
    return result;
  }
  
  private hashSchema(schema: any): string {
    return JSON.stringify(schema); // Simple hash for now
  }
  
  private generateDefaultTransform() {
    // Simple field mapping for now
    return {
      output: {
        "location": "city",
        "city": "location"
      },
      input: {
        "temperature": "temp",
        "humidity": "humid",
        "location": "city",
        "temp": "temperature",
        "humid": "humidity",
        "city": "location"
      }
    };
  }
  
  private async loadSchemaFromPaths(inputPath: string, outputPath: string): Promise<Result<SchemaData, RegistryError>> {
    // Convert relative paths to absolute
    const resolvedInputPath = this.resolvePath(inputPath);
    const resolvedOutputPath = this.resolvePath(outputPath);
    
    // Read input file
    try {
      const inputContent = await Deno.readTextFile(resolvedInputPath);
      // Continue with output file
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        return {
          ok: false,
          error: {
            type: 'SCHEMA_FILE_NOT_FOUND',
            message: `Schema file not found: ${resolvedInputPath}`
          }
        };
      }
      return {
        ok: false,
        error: {
          type: 'SCHEMA_FILE_NOT_FOUND',
          message: `Error reading schema file: ${resolvedInputPath}`,
          details: error
        }
      };
    }

    // Read files again to get content
    let inputContent: string, outputContent: string;
    try {
      inputContent = await Deno.readTextFile(resolvedInputPath);
    } catch {
      return {
        ok: false,
        error: {
          type: 'SCHEMA_FILE_NOT_FOUND',
          message: `Cannot read input schema file: ${resolvedInputPath}`
        }
      };
    }

    try {
      outputContent = await Deno.readTextFile(resolvedOutputPath);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        return {
          ok: false,
          error: {
            type: 'SCHEMA_FILE_NOT_FOUND',
            message: `Schema file not found: ${resolvedOutputPath}`
          }
        };
      }
      return {
        ok: false,
        error: {
          type: 'SCHEMA_FILE_NOT_FOUND',
          message: `Error reading schema file: ${resolvedOutputPath}`,
          details: error
        }
      };
    }
    
    // Parse JSON
    let inputSchema: JsonSchema, outputSchema: JsonSchema;
    try {
      inputSchema = JSON.parse(inputContent);
    } catch {
      return {
        ok: false,
        error: {
          type: 'INVALID_JSON',
          message: `Invalid JSON in file: ${resolvedInputPath}`
        }
      };
    }
    
    try {
      outputSchema = JSON.parse(outputContent);
    } catch {
      return {
        ok: false,
        error: {
          type: 'INVALID_JSON',
          message: `Invalid JSON in file: ${resolvedOutputPath}`
        }
      };
    }
    
    // Validate JSON Schema format
    const inputValidation = this.validateJsonSchema(inputSchema, resolvedInputPath);
    if (!inputValidation.ok) {
      return inputValidation;
    }

    const outputValidation = this.validateJsonSchema(outputSchema, resolvedOutputPath);
    if (!outputValidation.ok) {
      return outputValidation;
    }
    
    return {
      ok: true,
      data: {
        input: inputSchema,
        output: outputSchema
      }
    };
  }
  
  private resolvePath(path: string): string {
    // Handle relative paths
    if (path.startsWith("./") || path.startsWith("../")) {
      return new URL(path, `file://${Deno.cwd()}/`).pathname;
    }
    return path;
  }
  
  private validateJsonSchema(schema: any, path: string): Result<void, RegistryError> {
    // Basic JSON Schema validation
    if (typeof schema !== "object" || schema === null) {
      return {
        ok: false,
        error: {
          type: 'INVALID_SCHEMA',
          message: `Invalid JSON Schema in ${path}: must be an object`
        }
      };
    }
    
    // Check for type or properties (basic schema structure)
    if (!schema.type && !schema.properties && !schema.$ref && !schema.allOf && !schema.anyOf && !schema.oneOf) {
      return {
        ok: false,
        error: {
          type: 'INVALID_SCHEMA',
          message: `Invalid JSON Schema in ${path}: missing type or properties`
        }
      };
    }

    return { ok: true, data: undefined };
  }
}