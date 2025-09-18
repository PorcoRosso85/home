'use server';

import { getHonoContext } from '../../waku.hono-enhancer';

interface SubmissionResponse {
  success: boolean;
  message: string;
  filename?: string;
}

interface SubmissionData {
  name: string;
  email: string;
  subject: string;
  message: string;
  timestamp: string;
  submissionId: string;
}

/**
 * Generates a UUID v4 string
 */
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Server action that accepts form data and stores it as JSON in R2
 * Storage pattern: submissions/YYYY/MM/DD/timestamp-uuid.json
 */
export async function submitToR2(formData: FormData): Promise<SubmissionResponse> {
  try {
    // Get Hono context to access Cloudflare bindings
    const ctx = getHonoContext();
    
    if (!ctx) {
      console.error('Failed to get Hono context');
      return {
        success: false,
        message: 'Server configuration error'
      };
    }

    // Access the R2 bucket from Cloudflare environment
    const env = ctx.env as any;
    const bucket = env.DATA_BUCKET;
    
    if (!bucket) {
      console.error('R2 bucket not found in environment');
      return {
        success: false,
        message: 'Storage service not available'
      };
    }

    // Extract form data
    const name = formData.get('name')?.toString() || '';
    const email = formData.get('email')?.toString() || '';
    const subject = formData.get('subject')?.toString() || '';
    const message = formData.get('message')?.toString() || '';

    // Validate required fields
    if (!name || !email || !subject || !message) {
      return {
        success: false,
        message: 'All fields are required'
      };
    }

    // Generate timestamp and UUID
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5); // Format: 2025-01-28T15-30-45
    const uuid = generateUUID();

    // Create submission data
    const submissionData: SubmissionData = {
      name,
      email,
      subject,
      message,
      timestamp: now.toISOString(),
      submissionId: uuid
    };

    // Generate file path: submissions/YYYY/MM/DD/timestamp-uuid.json
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const filename = `submissions/${year}/${month}/${day}/${timestamp}-${uuid}.json`;

    // Convert data to JSON
    const jsonData = JSON.stringify(submissionData, null, 2);

    // Store in R2
    await bucket.put(filename, jsonData, {
      httpMetadata: {
        contentType: 'application/json',
        contentEncoding: 'utf-8',
      },
      customMetadata: {
        submissionId: uuid,
        submittedAt: now.toISOString(),
        name: name,
        email: email,
        subject: subject,
      }
    });

    console.log(`Successfully stored submission: ${filename}`);
    
    return {
      success: true,
      message: 'Feedback submitted successfully!',
      filename
    };

  } catch (error) {
    console.error('Error submitting to R2:', error);
    
    return {
      success: false,
      message: 'Failed to submit feedback. Please try again.'
    };
  }
}