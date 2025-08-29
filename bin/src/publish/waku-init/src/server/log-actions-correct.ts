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
 * Workers環境で動作する正しい実装
 * ファイルシステムは使わず、以下を使用：
 * 1. console.log → Cloudflare Logs
 * 2. KV/D1/R2 → 永続化
 * 3. Analytics Engine → 分析
 */
export async function submitAsLogCorrect(formData: FormData): Promise<SubmissionResponse> {
  try {
    const ctx = getHonoContext();
    if (!ctx) {
      return {
        success: false,
        message: 'Server context not available'
      };
    }

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

    // ✅ Workers環境で動作: console.log → Cloudflare Logs
    console.log(JSON.stringify(logEntry));

    // オプション1: KVに一時保存（バッファリング）
    const env = ctx.env as any;
    if (env.SUBMISSIONS_KV) {
      const key = `pending:${now.toISOString().split('T')[0]}:${id}`;
      await env.SUBMISSIONS_KV.put(key, JSON.stringify(logEntry), {
        expirationTtl: 86400 // 24時間後に自動削除
      });
    }

    // オプション2: D1データベースに保存
    if (env.DB) {
      await env.DB.prepare(
        'INSERT INTO submissions (id, data, created_at) VALUES (?, ?, ?)'
      ).bind(id, JSON.stringify(logEntry.data), now.toISOString()).run();
    }

    // オプション3: Analytics Engineに送信
    if (env.ANALYTICS) {
      env.ANALYTICS.writeDataPoint({
        blobs: [logEntry.data.email, logEntry.data.name],
        doubles: [Date.now()],
        indexes: [logEntry.data.id]
      });
    }

    // オプション4: Durable Objectsでバッファリング
    if (env.SUBMISSION_BUFFER) {
      const id = env.SUBMISSION_BUFFER.idFromName('main');
      const stub = env.SUBMISSION_BUFFER.get(id);
      await stub.fetch(new Request('https://buffer/add', {
        method: 'POST',
        body: JSON.stringify(logEntry)
      }));
    }

    return {
      success: true,
      message: 'Submission logged to Cloudflare',
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
 * Scheduled Workerでバッチ処理（cron実行）
 */
export async function scheduledBatchProcess(env: any) {
  // KVから pending エントリを取得
  const list = await env.SUBMISSIONS_KV.list({ prefix: 'pending:' });
  
  const logs: LogEntry[] = [];
  for (const key of list.keys) {
    const value = await env.SUBMISSIONS_KV.get(key.name);
    if (value) {
      logs.push(JSON.parse(value));
      // 処理後に削除
      await env.SUBMISSIONS_KV.delete(key.name);
    }
  }

  if (logs.length > 0) {
    // R2にJSONL形式で保存
    const date = new Date().toISOString().split('T')[0];
    const jsonl = logs.map(l => JSON.stringify(l)).join('\n');
    await env.DATA_BUCKET.put(
      `logs/${date}.jsonl`,
      jsonl,
      {
        httpMetadata: {
          contentType: 'application/x-ndjson'
        }
      }
    );
    
    console.log(`Batch processed ${logs.length} logs to R2`);
  }
}