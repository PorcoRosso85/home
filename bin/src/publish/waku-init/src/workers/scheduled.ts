/**
 * Scheduled Worker for batch processing logs
 * Runs via cron trigger defined in wrangler.toml
 */

interface Env {
  SUBMISSIONS_KV: KVNamespace;
  DATA_BUCKET: R2Bucket;
}

export default {
  async scheduled(
    controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    console.log('Starting scheduled batch processing...');
    
    try {
      // List all log entries
      const list = await env.SUBMISSIONS_KV.list({ prefix: 'log:' });
      
      if (list.keys.length === 0) {
        console.log('No logs to process');
        return;
      }
      
      const logs: any[] = [];
      const keysToDelete: string[] = [];
      
      // Fetch all logs
      for (const key of list.keys) {
        const value = await env.SUBMISSIONS_KV.get(key.name);
        if (value) {
          logs.push(JSON.parse(value));
          keysToDelete.push(key.name);
        }
      }
      
      // Create JSONL content
      const jsonl = logs.map(log => JSON.stringify(log)).join('\n');
      const date = new Date().toISOString().split('T')[0];
      const timestamp = Date.now();
      const filename = `logs/${date}/batch-${timestamp}.jsonl`;
      
      // Store to R2
      await env.DATA_BUCKET.put(filename, jsonl, {
        httpMetadata: {
          contentType: 'application/x-ndjson',
          contentEncoding: 'utf-8'
        },
        customMetadata: {
          processedAt: new Date().toISOString(),
          logCount: logs.length.toString()
        }
      });
      
      // Delete processed logs from KV
      for (const key of keysToDelete) {
        await env.SUBMISSIONS_KV.delete(key);
      }
      
      console.log(`Batch processed ${logs.length} logs to ${filename}`);
      
    } catch (error) {
      console.error('Batch processing error:', error);
      // In production, you might want to send this to an error tracking service
    }
  }
};