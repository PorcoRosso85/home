/**
 * Command-based Multi-Flake Contract
 * 
 * Pure contract definitions for command-based architecture.
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
 * Command Flake Contract
 * Commands are referenced by name only - Nix handles PATH resolution
 */
export const CommandFlakeContractSchema = z.object({
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
    'path-managed',      // Command-based: Nix manages PATH
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
export const GoProducerContract = CommandFlakeContractSchema.parse({
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
export const BunConsumerContract = CommandFlakeContractSchema.parse({
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
 * Command Validator - Contract validation only
 */
export class CommandValidator {
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
    producer: z.infer<typeof CommandFlakeContractSchema>,
    consumer: z.infer<typeof CommandFlakeContractSchema>
  ): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    
    // Check required commands exist (by name only)
    for (const [key, required] of Object.entries(consumer.commands)) {
      const provided = producer.commands[key];
      if (!provided || !this.validateCommand(required, provided)) {
        errors.push(`Command '${required.command}' not provided`);
      }
    }
    
    // Both must be path-managed for command-based architecture
    if (!producer.capabilities.includes('path-managed')) {
      errors.push('Producer must be path-managed for command-based architecture');
    }
    if (!consumer.capabilities.includes('path-managed')) {
      errors.push('Consumer must be path-managed for command-based architecture');
    }
    
    if (errors.length > 0) {
      return { valid: false, errors };
    }
    
    return { valid: true };
  }
}

// Type exports
export type CommandContract = z.infer<typeof CommandContractSchema>;
export type CommandFlakeContract = z.infer<typeof CommandFlakeContractSchema>;