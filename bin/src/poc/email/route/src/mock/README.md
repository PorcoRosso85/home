# ForwardableEmailMessage Mock Implementation

This directory contains a mock implementation of Cloudflare's `ForwardableEmailMessage` interface, designed for testing and development of Email Workers locally.

## Files

- **`ForwardableEmailMessage.js`** - Main mock implementation
- **`README.md`** - This documentation file

## Features

### Full Cloudflare Interface Compatibility

The mock implements the complete [Cloudflare Email Workers Runtime API](https://developers.cloudflare.com/email-routing/email-workers/runtime-api/):

```typescript
interface ForwardableEmailMessage {
  readonly from: string;
  readonly to: string;
  readonly headers: Headers;
  readonly raw: ReadableStream;
  readonly rawSize: number;
  
  setReject(reason: string): void;
  forward(rcptTo: string, headers?: Headers): Promise<void>;
  reply(message: EmailMessage): Promise<void>;
}
```

### Dual Raw Access Support

The mock uniquely supports both the official Cloudflare interface and the common usage pattern:

- **Property access**: `message.raw` (ReadableStream)
- **Method access**: `message.raw()` (returns Promise<ArrayBuffer>)

This compatibility layer ensures the mock works with existing code that expects either pattern.

### Content Type Support

- **String**: Plain text email content
- **ArrayBuffer**: Binary email data
- **ReadableStream**: Streaming email content

### State Tracking for Testing

Additional methods for testing and debugging:

- `getState()` - Returns current message state
- `reset()` - Resets message to initial state

## Usage Examples

### Basic Usage

```javascript
import { createMockEmailMessage } from './mock/ForwardableEmailMessage.js';

// Create a mock email message
const message = createMockEmailMessage({
  from: 'sender@example.com',
  to: 'recipient@example.com',
  subject: 'Test Email',
  content: 'Hello, this is a test message!'
});

// Use with Email Worker
export default {
  async email(message, env, ctx) {
    // Forward the email
    await message.forward('archive@example.com');
    
    // Or reject it
    message.setReject('Spam detected');
    
    // Or reply
    await message.reply({
      from: 'noreply@example.com',
      to: message.from
    });
  }
};
```

### Advanced Construction

```javascript
import { ForwardableEmailMessage } from './mock/ForwardableEmailMessage.js';

// From string content
const message1 = new ForwardableEmailMessage(
  'sender@example.com',
  'recipient@example.com',
  'Raw email content as string'
);

// From ArrayBuffer
const encoder = new TextEncoder();
const buffer = encoder.encode('Email content').buffer;
const message2 = new ForwardableEmailMessage(
  'sender@example.com', 
  'recipient@example.com',
  buffer
);

// From ReadableStream
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue(encoder.encode('Streaming content'));
    controller.close();
  }
});
const message3 = new ForwardableEmailMessage(
  'sender@example.com',
  'recipient@example.com', 
  stream
);
```

### Testing with State Tracking

```javascript
// Check message state during testing
const message = createMockEmailMessage();

console.log(message.getState());
// { rejected: false, forwarded: false, replies: [], ... }

await message.forward('test@example.com');

console.log(message.getState());
// { rejected: false, forwarded: true, forwardDestinations: [{ destination: 'test@example.com', ... }], ... }

// Reset for next test
message.reset();
```

### Integration with Existing Workers

The mock is designed to be a drop-in replacement for real Cloudflare ForwardableEmailMessage objects:

```javascript
import worker from '../index.js';
import { createMockEmailMessage } from './mock/ForwardableEmailMessage.js';

// Test existing worker with mock message
const mockMessage = createMockEmailMessage({
  from: 'test@example.com',
  to: 'worker@example.com'
});

const mockEnv = { /* your environment variables */ };
const mockCtx = { waitUntil: (promise) => promise };

// This will work with your existing worker code
const response = await worker.email(mockMessage, mockEnv, mockCtx);
```

## Validation Features

### Email Address Validation
- Validates email format in forward() and reply()
- Ensures proper addressing

### Header Validation  
- Only allows X-* headers in forward() extra headers
- Follows Cloudflare Email Workers restrictions

### State Management
- Prevents reject after forward
- Prevents forward after reject
- Tracks all operations for debugging

## Error Handling

The mock provides comprehensive error handling:

```javascript
// Invalid email addresses
await message.forward('invalid-email'); // throws Error

// Invalid headers
const badHeaders = new Headers({ 'Content-Type': 'text/html' });
await message.forward('test@example.com', badHeaders); // throws Error

// Invalid state transitions
await message.forward('test@example.com');
message.setReject('reason'); // throws Error
```

## Testing Integration

The mock includes comprehensive test files:

- `test/test_mock_email.js` - Unit tests for mock functionality
- `test/test_worker_compatibility.js` - Integration tests with existing worker

Run tests with:
```bash
node test/test_mock_email.js
node test/test_worker_compatibility.js
```

## Implementation Notes

### Compatibility Layer
The `raw` property uses a sophisticated compatibility layer that allows it to function both as a ReadableStream property (Cloudflare spec) and as a callable method (common usage pattern).

### Memory Management  
Content is cached after first access to avoid re-reading streams, improving performance in testing scenarios.

### Realistic Behavior
The mock simulates realistic email processing behavior, including:
- Proper MIME header handling
- Realistic raw email content generation
- Asynchronous operation simulation

This mock implementation enables comprehensive local testing of Email Workers without requiring Cloudflare infrastructure.