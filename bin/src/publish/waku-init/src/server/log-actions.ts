'use server';

/**
 * Simplified log-based form submission
 * Direct logging to Cloudflare Logs without KV buffering
 */
export async function submitAsLog(formData: FormData) {
  const logEntry = {
    type: 'form_submission',
    version: 1,
    timestamp: Date.now(),
    data: {
      id: crypto.randomUUID(),
      name: formData.get('name')?.toString() || '',
      email: formData.get('email')?.toString() || '',
      subject: formData.get('subject')?.toString() || '',
      message: formData.get('message')?.toString() || '',
      submittedAt: new Date().toISOString(),
    }
  };

  // Direct log to Cloudflare Logs (no KV needed)
  console.log(JSON.stringify(logEntry));

  return {
    success: true,
    message: 'Submission logged',
    logId: logEntry.data.id
  };
}

/**
 * Batch processing is handled by Cloudflare Logpush
 * No manual batching needed - logs are automatically sent to R2/S3
 * Configure Logpush in Cloudflare Dashboard for production use
 */
export async function batchProcessLogs() {
  console.log('Batch processing is handled by Cloudflare Logpush');
  return {
    processed: 0,
    outputKey: 'Use Cloudflare Logpush for automatic log aggregation'
  };
}