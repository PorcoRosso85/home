/**
 * Mock implementation of Cloudflare's ForwardableEmailMessage interface
 * Compatible with the Email Workers Runtime API
 * 
 * @see https://developers.cloudflare.com/email-routing/email-workers/runtime-api/
 */

export class ForwardableEmailMessage {
  /**
   * @param {string} from - Envelope From attribute
   * @param {string} to - Envelope To attribute  
   * @param {ReadableStream|string|ArrayBuffer} raw - Email message content
   * @param {Headers} [headers] - Optional headers object
   */
  constructor(from, to, raw, headers = new Headers()) {
    this.from = from;
    this.to = to;
    this.headers = headers;
    
    // Handle different raw content types and create both property and method
    if (typeof raw === 'string') {
      const encoder = new TextEncoder();
      const bytes = encoder.encode(raw);
      this.rawSize = bytes.length;
      this._rawContent = bytes;
      // Store as ReadableStream property (Cloudflare interface)
      this._rawStream = new ReadableStream({
        start(controller) {
          controller.enqueue(bytes);
          controller.close();
        }
      });
    } else if (raw instanceof ArrayBuffer) {
      this.rawSize = raw.byteLength;
      this._rawContent = new Uint8Array(raw);
      this._rawStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new Uint8Array(raw));
          controller.close();
        }
      });
    } else if (raw instanceof ReadableStream) {
      this._rawStream = raw;
      this.rawSize = 0; // Will be calculated when content is read
      this._rawContent = null;
    } else {
      throw new Error('Raw content must be a string, ArrayBuffer, or ReadableStream');
    }

    // Add compatibility: both property and method access to raw content
    Object.defineProperty(this, 'raw', {
      value: this._createRawCompatibility(),
      writable: false,
      enumerable: true,
      configurable: false
    });

    // Internal state tracking
    this._rejected = false;
    this._rejectReason = null;
    this._forwarded = false;
    this._forwardDestinations = [];
    this._replies = [];
  }

  /**
   * Create compatibility object that works both as ReadableStream property and callable method
   * This allows both: message.raw (ReadableStream) and message.raw() (method returning ArrayBuffer)
   * @private
   */
  _createRawCompatibility() {
    const self = this;
    
    // Create a function that can be called like message.raw()
    async function rawMethod() {
      if (self._rawContent) {
        return self._rawContent.buffer || self._rawContent;
      }

      // Read from ReadableStream if not cached
      const reader = self._rawStream.getReader();
      const chunks = [];
      let totalSize = 0;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          chunks.push(value);
          totalSize += value.length;
        }
      } finally {
        reader.releaseLock();
      }

      // Combine chunks into single ArrayBuffer
      const combined = new Uint8Array(totalSize);
      let offset = 0;
      for (const chunk of chunks) {
        combined.set(chunk, offset);
        offset += chunk.length;
      }

      self._rawContent = combined;
      self.rawSize = totalSize;
      
      return combined.buffer;
    }

    // Also make it behave like a ReadableStream when accessed as property
    // Copy ReadableStream methods to the function
    const streamMethods = ['getReader', 'cancel', 'locked', 'pipeTo', 'pipeThrough', 'tee'];
    for (const method of streamMethods) {
      if (typeof self._rawStream[method] === 'function') {
        rawMethod[method] = self._rawStream[method].bind(self._rawStream);
      }
    }

    return rawMethod;
  }

  /**
   * Reject this email message with a permanent SMTP error
   * @param {string} reason - Rejection reason
   */
  setReject(reason) {
    if (this._forwarded) {
      throw new Error('Cannot reject a message that has already been forwarded');
    }
    
    this._rejected = true;
    this._rejectReason = reason;
    
    console.log(`[MockEmail] Message rejected: ${reason}`);
  }

  /**
   * Forward this email message to a verified destination address
   * @param {string} rcptTo - Destination email address
   * @param {Headers} [extraHeaders] - Optional extra headers (X-* only)
   * @returns {Promise<void>}
   */
  async forward(rcptTo, extraHeaders) {
    if (this._rejected) {
      throw new Error('Cannot forward a rejected message');
    }

    // Validate destination email format
    if (!rcptTo || typeof rcptTo !== 'string' || !rcptTo.includes('@')) {
      throw new Error('Invalid destination email address');
    }

    // Validate extra headers (only X-* headers allowed)
    if (extraHeaders) {
      for (const [key] of extraHeaders.entries()) {
        if (!key.toLowerCase().startsWith('x-')) {
          throw new Error(`Invalid header: ${key}. Only X-* headers are allowed`);
        }
      }
    }

    this._forwarded = true;
    this._forwardDestinations.push({
      destination: rcptTo,
      headers: extraHeaders ? Object.fromEntries(extraHeaders.entries()) : null,
      timestamp: new Date().toISOString()
    });

    console.log(`[MockEmail] Message forwarded to: ${rcptTo}`);
    
    // Simulate async operation
    return new Promise(resolve => setTimeout(resolve, 10));
  }

  /**
   * Reply to the sender with a new email message
   * @param {EmailMessage} message - Reply message
   * @returns {Promise<void>}
   */
  async reply(message) {
    if (this._rejected) {
      throw new Error('Cannot reply to a rejected message');
    }

    // Validate EmailMessage structure
    if (!message || typeof message !== 'object') {
      throw new Error('Reply message must be an EmailMessage object');
    }
    
    if (!message.from || !message.to) {
      throw new Error('Reply message must have from and to properties');
    }

    // Validate email addresses
    if (!message.from.includes('@') || !message.to.includes('@')) {
      throw new Error('Invalid email addresses in reply message');
    }

    this._replies.push({
      from: message.from,
      to: message.to,
      timestamp: new Date().toISOString(),
      originalMessage: message
    });

    console.log(`[MockEmail] Reply sent from ${message.from} to ${message.to}`);
    
    // Simulate async operation
    return new Promise(resolve => setTimeout(resolve, 10));
  }


  /**
   * Get the current state of the message (for testing/debugging)
   * @returns {Object}
   */
  getState() {
    return {
      from: this.from,
      to: this.to,
      rawSize: this.rawSize,
      rejected: this._rejected,
      rejectReason: this._rejectReason,
      forwarded: this._forwarded,
      forwardDestinations: [...this._forwardDestinations],
      replies: [...this._replies],
      headerCount: Array.from(this.headers.entries()).length
    };
  }

  /**
   * Reset message state (for testing)
   */
  reset() {
    this._rejected = false;
    this._rejectReason = null;
    this._forwarded = false;
    this._forwardDestinations = [];
    this._replies = [];
  }
}

/**
 * Simple EmailMessage implementation for replies
 */
export class EmailMessage {
  /**
   * @param {string} from - Sender email address
   * @param {string} to - Recipient email address
   * @param {Object} [options] - Additional options
   */
  constructor(from, to, options = {}) {
    if (!from || !to) {
      throw new Error('EmailMessage requires from and to addresses');
    }
    
    this.from = from;
    this.to = to;
    this.subject = options.subject || '';
    this.content = options.content || '';
    this.headers = options.headers || {};
  }
}

/**
 * Factory function to create mock ForwardableEmailMessage instances
 * @param {Object} options - Message options
 * @returns {ForwardableEmailMessage}
 */
export function createMockEmailMessage(options = {}) {
  const {
    from = 'sender@example.com',
    to = 'recipient@example.com',
    subject = 'Test Message',
    content = 'This is a test email message.',
    headers = {}
  } = options;

  // Create Headers object
  const messageHeaders = new Headers({
    'Message-ID': `<test-${Date.now()}@example.com>`,
    'Date': new Date().toUTCString(),
    'Subject': subject,
    'From': from,
    'To': to,
    'Content-Type': 'text/plain; charset=UTF-8',
    ...headers
  });

  // Create raw email content
  const rawContent = [
    `Message-ID: <test-${Date.now()}@example.com>`,
    `Date: ${new Date().toUTCString()}`,
    `From: ${from}`,
    `To: ${to}`,
    `Subject: ${subject}`,
    'Content-Type: text/plain; charset=UTF-8',
    '',
    content
  ].join('\r\n');

  return new ForwardableEmailMessage(from, to, rawContent, messageHeaders);
}

export default ForwardableEmailMessage;