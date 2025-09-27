/**
 * Data Consumer Contract using Zod
 * 
 * Defines the input requirements and output contracts for the data consumer flake
 */

import { z } from 'zod';
import { DataProviderOutputSchema } from './data-provider.contract';

// Input requirement (matches provider output)
export const ConsumerInputSchema = DataProviderOutputSchema;

// Output schemas for different operations
export const SummaryOutputSchema = z.object({
  total_products: z.number().int().nonnegative(),
  categories: z.array(z.enum(["hardware", "software"])),
  total_value: z.number().nonnegative(),
  timestamp: z.string().datetime()
});

export const FilteredProductsSchema = z.array(
  z.object({
    id: z.string(),
    name: z.string(),
    price: z.number(),
    category: z.enum(["hardware", "software"]),
    metadata: z.record(z.unknown())
  })
);

export const TotalValueSchema = z.number().nonnegative();

// Operation result union
export const ConsumerOutputSchema = z.union([
  SummaryOutputSchema,
  FilteredProductsSchema,
  TotalValueSchema
]);

// Contract definition for the consumer
export const DataConsumerContractSchema = z.object({
  version: z.string(),
  type: z.literal("data-consumer"),
  inputs: z.object({
    data: z.object({
      format: z.literal("json"),
      schema: z.literal("products"),
      required: z.literal(true)
    })
  }),
  outputs: z.object({
    summary: z.object({
      format: z.literal("json"),
      operations: z.array(z.enum(["summarize", "filter-category", "calculate-total"]))
    })
  }),
  capabilities: z.array(z.enum(["data-processor", "json", "jq"]))
});

// Operation definitions
export enum ConsumerOperation {
  SUMMARIZE = "summarize",
  FILTER_CATEGORY = "filter-category",
  CALCULATE_TOTAL = "calculate-total"
}

// Type exports
export type ConsumerInput = z.infer<typeof ConsumerInputSchema>;
export type SummaryOutput = z.infer<typeof SummaryOutputSchema>;
export type FilteredProducts = z.infer<typeof FilteredProductsSchema>;
export type TotalValue = z.infer<typeof TotalValueSchema>;
export type ConsumerOutput = z.infer<typeof ConsumerOutputSchema>;
export type DataConsumerContract = z.infer<typeof DataConsumerContractSchema>;

// Validation functions
export function validateConsumerInput(data: unknown): ConsumerInput {
  return ConsumerInputSchema.parse(data);
}

export function validateSummaryOutput(data: unknown): SummaryOutput {
  return SummaryOutputSchema.parse(data);
}

export function validateFilteredProducts(data: unknown): FilteredProducts {
  return FilteredProductsSchema.parse(data);
}

export function validateTotalValue(data: unknown): TotalValue {
  return TotalValueSchema.parse(data);
}

export function validateConsumerContract(contract: unknown): DataConsumerContract {
  return DataConsumerContractSchema.parse(contract);
}

// Operation result validators
export function validateOperationResult(operation: ConsumerOperation, result: unknown): ConsumerOutput {
  switch (operation) {
    case ConsumerOperation.SUMMARIZE:
      return validateSummaryOutput(result);
    case ConsumerOperation.FILTER_CATEGORY:
      return validateFilteredProducts(result);
    case ConsumerOperation.CALCULATE_TOTAL:
      return validateTotalValue(result);
    default:
      throw new Error(`Unknown operation: ${operation}`);
  }
}