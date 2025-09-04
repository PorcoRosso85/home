/**
 * Level 3 Multi-Flake Contract
 * 
 * Pure contract definitions for Level 3 architecture.
 * No path information - only command names and data contracts.
 */

import { z } from 'zod';

/**
 * Command Contract - defines available commands (not paths)
 */
export const CommandContractSchema = z.object({
  command: z.string().min(1),  // Command name only (e.g., 'my-go-app')
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
  capabilities: z.array(z.string())
});

/**
 * Level 3 Flake Contract
 * Commands are referenced by name only - Nix handles PATH resolution
 */
export const Level3FlakeContractSchema = z.object({
  version: z.string(),
  type: z.enum(['producer', 'consumer', 'transformer']),
  
  // Commands provided (producer) or required (consumer)
  commands: z.record(z.string(), CommandContractSchema),
  
  // Pure data contracts - no path information
  interface: z.object({
    inputs: z.record(z.string(), z.any()),
    outputs: z.record(z.string(), z.any())
  }),
  
  // Runtime capabilities (path-managed means Nix handles paths)
  capabilities: z.array(z.enum([
    'path-managed',      // Level 3: Nix manages PATH
    'pure-contract',     // No path information in contracts
    'command-based',     // Uses command names only
    'data-transformer',  // Transforms data
    'data-producer',     // Produces data
    'data-consumer'      // Consumes data
  ]))
});

/**
 * Example: Go Producer Contract
 */
export const GoProducerContract = Level3FlakeContractSchema.parse({
  version: '1.0.0',
  type: 'producer',
  commands: {
    processor: {
      command: 'my-go-processor',  // Just the command name
      version: '1.0.0',
      capabilities: ['json-processing', 'stream-processing']
    }
  },
  interface: {
    inputs: {
      data: z.object({
        items: z.array(z.any())
      })
    },
    outputs: {
      result: z.object({
        processed: z.number(),
        failed: z.number(),
        output: z.array(z.any())
      })
    }
  },
  capabilities: ['path-managed', 'pure-contract', 'data-transformer']
});

/**
 * Example: Bun Consumer Contract
 */
export const BunConsumerContract = Level3FlakeContractSchema.parse({
  version: '1.0.0',
  type: 'consumer',
  commands: {
    processor: {
      command: 'my-go-processor',  // Same command name - no path
      version: '1.0.0',
      capabilities: ['json-processing']
    }
  },
  interface: {
    inputs: {
      rawData: z.array(z.any())
    },
    outputs: {
      report: z.object({
        summary: z.string(),
        details: z.any()
      })
    }
  },
  capabilities: ['path-managed', 'pure-contract', 'data-consumer']
});

/**
 * Level 3 Glue - Ultra-thin validation only
 */
export class Level3Glue {
  /**
   * Validate command availability (name only, not path)
   */
  validateCommand(required: CommandContract, provided: CommandContract): boolean {
    // Only check command name matches - Nix handles the path
    return required.command === provided.command;
  }
  
  /**
   * Validate contract compatibility
   */
  validateCompatibility(
    producer: z.infer<typeof Level3FlakeContractSchema>,
    consumer: z.infer<typeof Level3FlakeContractSchema>
  ): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    
    // Check required commands exist (by name only)
    for (const [key, required] of Object.entries(consumer.commands)) {
      const provided = producer.commands[key];
      if (!provided || !this.validateCommand(required, provided)) {
        errors.push(`Command '${required.command}' not provided`);
      }
    }
    
    // Both must be path-managed for Level 3
    if (!producer.capabilities.includes('path-managed')) {
      errors.push('Producer must be path-managed for Level 3');
    }
    if (!consumer.capabilities.includes('path-managed')) {
      errors.push('Consumer must be path-managed for Level 3');
    }
    
    if (errors.length > 0) {
      return { valid: false, errors };
    }
    
    return { valid: true };
  }
}

// Type exports
export type CommandContract = z.infer<typeof CommandContractSchema>;
export type Level3FlakeContract = z.infer<typeof Level3FlakeContractSchema>;