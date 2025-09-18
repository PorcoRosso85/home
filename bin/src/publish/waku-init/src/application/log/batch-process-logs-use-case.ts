import type {
  BatchProcessingResult,
  LogProcessingResult,
} from '../../domain/mod.js';

/**
 * Dependencies required by the batch process logs use case
 */
export interface BatchProcessLogsDependencies {
  /**
   * Logging service for informational messages
   */
  logger: {
    log: (message: string) => void;
  };
  /**
   * Configuration for log processing
   */
  config?: {
    /**
     * Provider used for log aggregation (e.g., 'cloudflare-logpush')
     */
    provider: string;
    /**
     * Destination for processed logs (e.g., R2 bucket path)
     */
    destination?: string;
  };
}

/**
 * Default configuration for Cloudflare Workers environment
 */
const DEFAULT_CONFIG = {
  provider: 'cloudflare-logpush',
  destination: 'Automatic R2/S3 destination via Cloudflare Dashboard configuration',
} as const;

/**
 * Batch Process Logs Use Case
 * 
 * Handles batch processing of logs in a Cloudflare Workers environment:
 * - In Workers, batch processing is handled automatically by Cloudflare Logpush
 * - This use case provides information about the automatic processing
 * - Returns status information for monitoring/debugging purposes
 * 
 * Note: Manual batch processing is not needed in Workers as Logpush
 * automatically aggregates logs and sends them to configured destinations
 */
export async function batchProcessLogsUseCase(
  dependencies: BatchProcessLogsDependencies
): Promise<BatchProcessingResult> {
  try {
    const config = { ...DEFAULT_CONFIG, ...dependencies.config };

    // Log information about the automatic processing
    const infoMessage = `Batch processing is handled by ${config.provider}`;
    dependencies.logger.log(infoMessage);

    // Additional info for monitoring
    const detailedInfo = {
      provider: config.provider,
      destination: config.destination,
      automatic: true,
      manualProcessingRequired: false,
      configurationLocation: 'Cloudflare Dashboard > Analytics & Logs > Logpush',
    };

    dependencies.logger.log(`Processing details: ${JSON.stringify(detailedInfo, null, 2)}`);

    // Return result indicating automatic processing
    const result: BatchProcessingResult = {
      processed: 0, // 0 because processing is automatic
      outputKey: 'Use Cloudflare Logpush for automatic log aggregation',
    };

    return result;

  } catch (error) {
    console.error('Error in batchProcessLogsUseCase:', error);
    
    // Return a result even on error to maintain consistency
    return {
      processed: 0,
      outputKey: 'Error occurred during batch processing information retrieval',
    };
  }
}

/**
 * Get batch processing status information
 * 
 * Provides information about the current log processing configuration
 * and status in the Workers environment.
 */
export async function getBatchProcessingStatusUseCase(
  dependencies: BatchProcessLogsDependencies
): Promise<LogProcessingResult> {
  try {
    const config = { ...DEFAULT_CONFIG, ...dependencies.config };
    
    const statusInfo = {
      enabled: true,
      provider: config.provider,
      destination: config.destination,
      lastProcessedAt: null, // Not available in automatic processing
      nextProcessingAt: null, // Continuous processing
      status: 'active' as const,
      notes: 'Processing handled automatically by Cloudflare Logpush',
    };

    return {
      success: true,
      status: statusInfo,
      message: 'Batch processing status retrieved successfully',
    };

  } catch (error) {
    console.error('Error getting batch processing status:', error);
    
    return {
      success: false,
      status: null,
      message: 'Failed to retrieve batch processing status',
    };
  }
}