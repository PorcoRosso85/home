/**
 * Data Provider Contract using Zod
 * 
 * Defines the structured data output contract for the data provider flake
 */

import { z } from 'zod';

// Product metadata schemas
const HardwareMetadataSchema = z.object({
  weight: z.number().positive(),
  dimensions: z.tuple([z.number(), z.number(), z.number()])
});

const SoftwareMetadataSchema = z.object({
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
  license: z.string()
});

// Product schema with discriminated union for metadata
const ProductSchema = z.discriminatedUnion("category", [
  z.object({
    id: z.string().regex(/^prod-\d{3}$/),
    name: z.string().min(1),
    price: z.number().positive(),
    category: z.literal("hardware"),
    metadata: HardwareMetadataSchema
  }),
  z.object({
    id: z.string().regex(/^prod-\d{3}$/),
    name: z.string().min(1),
    price: z.number().positive(),
    category: z.literal("software"),
    metadata: SoftwareMetadataSchema
  })
]);

// Main data structure provided by the flake
export const DataProviderOutputSchema = z.object({
  products: z.array(ProductSchema),
  timestamp: z.string().datetime(),
  version: z.string().regex(/^\d+\.\d+\.\d+$/)
});

// Contract definition for the provider
export const DataProviderContractSchema = z.object({
  version: z.string(),
  type: z.literal("data-provider"),
  outputs: z.object({
    data: z.object({
      format: z.literal("json"),
      schema: z.literal("products"),
      path: z.string()
    })
  }),
  capabilities: z.array(z.enum(["data-source", "json", "static"]))
});

// Type exports
export type Product = z.infer<typeof ProductSchema>;
export type DataProviderOutput = z.infer<typeof DataProviderOutputSchema>;
export type DataProviderContract = z.infer<typeof DataProviderContractSchema>;

// Validation functions
export function validateProviderOutput(data: unknown): DataProviderOutput {
  return DataProviderOutputSchema.parse(data);
}

export function validateProviderContract(contract: unknown): DataProviderContract {
  return DataProviderContractSchema.parse(contract);
}

// Schema compatibility check
export function isCompatibleProviderData(data: unknown): boolean {
  try {
    DataProviderOutputSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}