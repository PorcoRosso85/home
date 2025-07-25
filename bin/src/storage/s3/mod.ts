/**
 * S3 Storage Module - LLM-first interface for S3 operations
 * 
 * This module provides a conversational interface for S3 operations,
 * accepting JSON input for various actions like upload, download, list, and delete.
 */

export { executeS3Command } from './application.ts';
export type { S3Command, S3Result, S3Config } from './domain.ts';