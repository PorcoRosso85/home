/**
 * TypeScript definitions for Email Archive Worker
 */

export interface EmailMetadata {
  messageId: string;
  originalMessageId: string;
  receivedAt: string;
  emailDate: string;
  from: string;
  to: string[];
  subject: string;
  size: number;
  contentType: string;
  isMultipart: boolean;
  headers: Record<string, string>;
  attachments?: AttachmentInfo[];
  archivedBy: string;
  workerVersion: string;
}

export interface AttachmentInfo {
  filename: string;
  contentType: string;
  detectedAt: string;
  size?: number;
}

export interface WorkerEnv {
  MINIO_ENDPOINT: string;
  MINIO_ACCESS_KEY: string;
  MINIO_SECRET_KEY: string;
  BUCKET_NAME: string;
}

export interface EmailMessage {
  from: string;
  to: string | string[];
  headers: Map<string, string>;
  raw(): Promise<ArrayBuffer>;
}

export interface EmailHandler {
  email(message: EmailMessage, env: WorkerEnv, ctx: ExecutionContext): Promise<Response>;
}

declare global {
  interface CloudflareWorkerGlobalScope {
    addEventListener(type: "email", handler: (event: EmailEvent) => void): void;
  }

  interface EmailEvent extends Event {
    message: EmailMessage;
    env: WorkerEnv;
    ctx: ExecutionContext;
  }
}