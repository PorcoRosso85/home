/**
 * Development Email Endpoint for Local Testing
 * Provides a /__email endpoint that accepts POST requests with email data
 * and converts them to ForwardableEmailMessage format for testing the Worker
 */

import { ForwardableEmailMessage, createMockEmailMessage } from '../mock/ForwardableEmailMessage.js';
import worker from '../index.js';

/**
 * Handle the /__email endpoint for local development
 * @param {Request} request - Incoming HTTP request
 * @param {Object} env - Environment variables
 * @param {Object} ctx - Execution context
 * @returns {Response}
 */
export async function handleEmailEndpoint(request, env, ctx) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed. Use POST to send email data.', {
      status: 405,
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  try {
    // Parse the incoming email data
    const contentType = request.headers.get('content-type') || '';
    let emailData;

    if (contentType.includes('application/json')) {
      // Structured email data
      emailData = await request.json();
    } else if (contentType.includes('text/plain') || contentType.includes('message/rfc822')) {
      // Raw email content
      const rawContent = await request.text();
      emailData = parseRawEmail(rawContent);
    } else {
      return new Response('Unsupported content type. Use application/json or text/plain.', {
        status: 400,
        headers: { 'Content-Type': 'text/plain' }
      });
    }

    // Validate required fields
    if (!emailData.from || !emailData.to) {
      return new Response('Missing required fields: from and to', {
        status: 400,
        headers: { 'Content-Type': 'text/plain' }
      });
    }

    console.log(`[DevEndpoint] Processing email from: ${emailData.from} to: ${emailData.to}`);

    // Convert to ForwardableEmailMessage
    const emailMessage = createForwardableEmailMessage(emailData);

    // Call the Worker's email handler
    const result = await worker.email(emailMessage, env, ctx);

    // Return the result
    return new Response(JSON.stringify({
      success: true,
      message: 'Email processed successfully',
      workerResponse: result.status,
      emailData: {
        from: emailData.from,
        to: emailData.to,
        subject: emailData.subject || '(No Subject)',
        messageId: emailMessage.getState().headerCount > 0 ? 'generated' : 'provided'
      }
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('[DevEndpoint] Error processing email:', error);
    
    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      stack: error.stack
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Create a ForwardableEmailMessage from structured email data
 * @param {Object} emailData - Email data object
 * @returns {ForwardableEmailMessage}
 */
function createForwardableEmailMessage(emailData) {
  const {
    from,
    to,
    subject = 'Test Email from Dev Endpoint',
    content = 'This email was sent via the development endpoint.',
    headers = {},
    raw = null
  } = emailData;

  // If raw email content is provided, use it directly
  if (raw) {
    const messageHeaders = new Headers();
    
    // Parse headers from raw content or use provided headers
    if (typeof headers === 'object' && headers !== null) {
      Object.entries(headers).forEach(([key, value]) => {
        messageHeaders.set(key, value);
      });
    }

    // Ensure basic headers are present
    if (!messageHeaders.has('Message-ID')) {
      messageHeaders.set('Message-ID', `<dev-${Date.now()}@localhost>`);
    }
    if (!messageHeaders.has('Date')) {
      messageHeaders.set('Date', new Date().toUTCString());
    }
    if (!messageHeaders.has('From')) {
      messageHeaders.set('From', from);
    }
    if (!messageHeaders.has('To')) {
      messageHeaders.set('To', to);
    }
    if (!messageHeaders.has('Subject')) {
      messageHeaders.set('Subject', subject);
    }

    return new ForwardableEmailMessage(from, to, raw, messageHeaders);
  }

  // Otherwise, create a mock email message
  return createMockEmailMessage({
    from,
    to,
    subject,
    content,
    headers: {
      'X-Dev-Endpoint': 'true',
      'X-Received-At': new Date().toISOString(),
      ...headers
    }
  });
}

/**
 * Parse raw email content to extract basic email data
 * @param {string} rawContent - Raw email content
 * @returns {Object} - Parsed email data
 */
function parseRawEmail(rawContent) {
  const lines = rawContent.split('\n');
  const emailData = {
    from: '',
    to: '',
    subject: '',
    content: '',
    headers: {}
  };

  let headerSection = true;
  let currentHeader = '';
  let contentLines = [];

  for (const line of lines) {
    if (headerSection) {
      if (line.trim() === '') {
        headerSection = false;
        continue;
      }

      // Handle header continuation lines
      if (line.startsWith(' ') || line.startsWith('\t')) {
        if (currentHeader) {
          emailData.headers[currentHeader] += ' ' + line.trim();
        }
        continue;
      }

      const colonIndex = line.indexOf(':');
      if (colonIndex > 0) {
        currentHeader = line.substring(0, colonIndex).trim().toLowerCase();
        const value = line.substring(colonIndex + 1).trim();
        
        emailData.headers[currentHeader] = value;
        
        // Extract key fields
        switch (currentHeader) {
          case 'from':
            emailData.from = extractEmailAddress(value);
            break;
          case 'to':
            emailData.to = extractEmailAddress(value);
            break;
          case 'subject':
            emailData.subject = value;
            break;
        }
      }
    } else {
      contentLines.push(line);
    }
  }

  emailData.content = contentLines.join('\n').trim();
  
  return emailData;
}

/**
 * Extract email address from header value
 * @param {string} headerValue - Header value that may contain name and email
 * @returns {string} - Extracted email address
 */
function extractEmailAddress(headerValue) {
  // Simple regex to extract email from "Name <email@domain.com>" format
  const emailMatch = headerValue.match(/<([^>]+)>/);
  if (emailMatch) {
    return emailMatch[1];
  }
  
  // If no angle brackets, assume the whole value is the email
  return headerValue.trim();
}

/**
 * Enhanced request handler that integrates with wrangler dev
 * @param {Request} request - Incoming HTTP request
 * @param {Object} env - Environment variables
 * @param {Object} ctx - Execution context
 * @returns {Response}
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle the email endpoint
    if (url.pathname === '/__email') {
      return handleEmailEndpoint(request, env, ctx);
    }
    
    // Handle health check
    if (url.pathname === '/__health') {
      return new Response(JSON.stringify({
        status: 'ok',
        timestamp: new Date().toISOString(),
        endpoints: {
          '/__email': 'POST - Send email data for processing',
          '/__health': 'GET - Health check'
        }
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Default response for other paths
    return new Response(JSON.stringify({
      message: 'Email Archive Worker Dev Endpoint',
      available_endpoints: {
        '/__email': 'POST - Send email data for processing',
        '/__health': 'GET - Health check'
      },
      usage: {
        structured_data: 'POST /__email with JSON: {"from": "sender@example.com", "to": "recipient@example.com", "subject": "Test", "content": "Message body"}',
        raw_email: 'POST /__email with Content-Type: text/plain and raw email content'
      }
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};