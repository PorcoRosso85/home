'use server';

import { getHonoContext } from '../../waku.hono-enhancer';

interface SubmissionResponse {
  success: boolean;
  message: string;
  logId?: string;
}

interface LogEntry {
  type: 'form_submission';
  version: 1;
  timestamp: number;
  data: {
    id: string;
    name: string;
    email: string;
    subject: string;
    message: string;
    submittedAt: string;
  };
}

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Log-based form submission (local simulation)
 * In production: outputs to stdout → Cloudflare Logs → Analytics Engine
 * In development: writes to local JSONL file
 */
export async function submitAsLog(formData: FormData): Promise<SubmissionResponse> {
  try {
    // Extract form data
    const id = generateUUID();
    const now = new Date();
    
    const logEntry: LogEntry = {
      type: 'form_submission',
      version: 1,
      timestamp: Date.now(),
      data: {
        id,
        name: formData.get('name')?.toString() || '',
        email: formData.get('email')?.toString() || '',
        subject: formData.get('subject')?.toString() || '',
        message: formData.get('message')?.toString() || '',
        submittedAt: now.toISOString(),
      }
    };

    // Workers環境: 構造化ログ出力（Cloudflare Logsへ）
    console.log(JSON.stringify(logEntry));
    
    // Optional: KVストレージに一時保存（バッファリング用）
    const ctx = getHonoContext();
    if (ctx?.env?.SUBMISSIONS_KV) {
      const key = `log:${now.toISOString()}:${id}`;
      await ctx.env.SUBMISSIONS_KV.put(key, JSON.stringify(logEntry), {
        expirationTtl: 86400 // 24時間後に自動削除
      });
    }

    return {
      success: true,
      message: 'Submission logged successfully',
      logId: id
    };

  } catch (error) {
    console.error('Error logging submission:', error);
    return {
      success: false,
      message: 'Failed to log submission'
    };
  }
}

/**
 * Batch processor for Workers environment
 * Aggregates logs from KV and stores to R2
 */
export async function batchProcessLogs(): Promise<{
  processed: number;
  outputKey: string;
}> {
  const ctx = getHonoContext();
  if (!ctx?.env?.SUBMISSIONS_KV || !ctx?.env?.DATA_BUCKET) {
    return {
      processed: 0,
      outputKey: ''
    };
  }

  // List all log entries from KV
  const list = await ctx.env.SUBMISSIONS_KV.list({ prefix: 'log:' });
  const allEntries: LogEntry[] = [];
  
  // Fetch and aggregate all logs
  for (const key of list.keys) {
    const value = await ctx.env.SUBMISSIONS_KV.get(key.name);
    if (value) {
      allEntries.push(JSON.parse(value));
      // Mark for deletion after processing
      await ctx.env.SUBMISSIONS_KV.delete(key.name);
    }
  }

  if (allEntries.length === 0) {
    return {
      processed: 0,
      outputKey: ''
    };
  }

  // Create JSONL content
  const jsonl = allEntries.map(e => JSON.stringify(e)).join('\n');
  const outputKey = `logs/batch-${Date.now()}.jsonl`;

  // Store to R2
  await ctx.env.DATA_BUCKET.put(outputKey, jsonl, {
    httpMetadata: {
      contentType: 'application/x-ndjson'
    }
  });

  return {
    processed: allEntries.length,
    outputKey
  };
}