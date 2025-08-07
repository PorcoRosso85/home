/**
 * Comprehensive test suite for ForwardableEmailMessage mock implementation
 * Tests all methods, edge cases, error handling, and Worker interface compatibility
 */

import { ForwardableEmailMessage, EmailMessage, createMockEmailMessage } from '../../src/mock/ForwardableEmailMessage.js';
import { strict as assert } from 'assert';

// Test utilities
class TestRunner {
  constructor() {
    this.testCount = 0;
    this.passCount = 0;
    this.failCount = 0;
    this.results = [];
  }

  async test(name, testFn) {
    this.testCount++;
    console.log(`\n🧪 Test ${this.testCount}: ${name}`);
    
    try {
      await testFn();
      this.passCount++;
      this.results.push({ name, status: 'PASS' });
      console.log(`   ✅ PASS`);
    } catch (error) {
      this.failCount++;
      this.results.push({ name, status: 'FAIL', error: error.message });
      console.log(`   ❌ FAIL: ${error.message}`);
      console.log(`   Stack: ${error.stack.split('\n')[1]?.trim()}`);
    }
  }

  summary() {
    console.log(`\n📊 Test Summary:`);
    console.log(`   Total: ${this.testCount}`);
    console.log(`   Passed: ${this.passCount}`);
    console.log(`   Failed: ${this.failCount}`);
    console.log(`   Success Rate: ${((this.passCount / this.testCount) * 100).toFixed(1)}%`);
    
    if (this.failCount > 0) {
      console.log(`\n❌ Failed Tests:`);
      this.results.filter(r => r.status === 'FAIL').forEach(r => {
        console.log(`   - ${r.name}: ${r.error}`);
      });
    }
    
    return this.failCount === 0;
  }
}

// Test fixture utilities
function createTestMessage(options = {}) {
  return createMockEmailMessage({
    from: 'test@example.com',
    to: 'recipient@example.com',
    subject: 'Test Message',
    content: 'This is a test email message.',
    ...options
  });
}

function createReadableStream(content) {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(content);
  
  return new ReadableStream({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    }
  });
}

async function runComprehensiveTests() {
  console.log('🚀 Starting Comprehensive ForwardableEmailMessage Test Suite\n');
  const runner = new TestRunner();

  // ========== Constructor Tests ==========
  
  await runner.test('Constructor - String content', async () => {
    const content = 'Test email content';
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', content);
    
    assert.strictEqual(message.from, 'from@test.com');
    assert.strictEqual(message.to, 'to@test.com');
    assert.strictEqual(message.rawSize, new TextEncoder().encode(content).length);
    assert(message.headers instanceof Headers);
  });

  await runner.test('Constructor - ArrayBuffer content', async () => {
    const content = 'Test content';
    const encoder = new TextEncoder();
    const buffer = encoder.encode(content).buffer;
    
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', buffer);
    
    assert.strictEqual(message.rawSize, buffer.byteLength);
    const rawResult = await message.raw();
    assert(rawResult instanceof ArrayBuffer);
    assert.strictEqual(rawResult.byteLength, buffer.byteLength);
  });

  await runner.test('Constructor - ReadableStream content', async () => {
    const content = 'Stream content';
    const stream = createReadableStream(content);
    
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', stream);
    
    assert.strictEqual(message.rawSize, 0); // Initially unknown
    const rawResult = await message.raw();
    assert(rawResult instanceof ArrayBuffer);
    assert.strictEqual(message.rawSize, new TextEncoder().encode(content).length);
  });

  await runner.test('Constructor - Invalid content type', async () => {
    assert.throws(() => {
      new ForwardableEmailMessage('from@test.com', 'to@test.com', 123);
    }, /Raw content must be a string, ArrayBuffer, or ReadableStream/);
  });

  await runner.test('Constructor - Custom headers', async () => {
    const headers = new Headers({ 'X-Custom': 'value' });
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', 'content', headers);
    
    assert.strictEqual(message.headers.get('X-Custom'), 'value');
  });

  // ========== Raw Content Access Tests ==========

  await runner.test('Raw - Method call returns ArrayBuffer', async () => {
    const message = createTestMessage();
    const rawResult = await message.raw();
    
    assert(rawResult instanceof ArrayBuffer);
    assert(rawResult.byteLength > 0);
  });

  await runner.test('Raw - ReadableStream property access', async () => {
    const message = createTestMessage();
    
    assert(typeof message.raw.getReader === 'function');
    assert(typeof message.raw.cancel === 'function');
    assert(typeof message.raw.locked === 'boolean');
  });

  await runner.test('Raw - Content consistency', async () => {
    const originalContent = 'Consistent test content';
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', originalContent);
    
    const rawResult = await message.raw();
    const decoded = new TextDecoder().decode(rawResult);
    
    assert(decoded.includes(originalContent));
  });

  await runner.test('Raw - Multiple calls return same content', async () => {
    const message = createTestMessage();
    
    const raw1 = await message.raw();
    const raw2 = await message.raw();
    
    assert.strictEqual(raw1.byteLength, raw2.byteLength);
    assert.deepStrictEqual(new Uint8Array(raw1), new Uint8Array(raw2));
  });

  // ========== Forward Method Tests ==========

  await runner.test('Forward - Basic functionality', async () => {
    const message = createTestMessage();
    
    await message.forward('destination@test.com');
    
    const state = message.getState();
    assert.strictEqual(state.forwarded, true);
    assert.strictEqual(state.forwardDestinations.length, 1);
    assert.strictEqual(state.forwardDestinations[0].destination, 'destination@test.com');
  });

  await runner.test('Forward - With extra headers', async () => {
    const message = createTestMessage();
    const headers = new Headers({
      'X-Custom-Header': 'test-value',
      'X-Forward-ID': '12345'
    });
    
    await message.forward('dest@test.com', headers);
    
    const state = message.getState();
    const destination = state.forwardDestinations[0];
    assert.strictEqual(destination.headers['X-Custom-Header'], 'test-value');
    assert.strictEqual(destination.headers['X-Forward-ID'], '12345');
  });

  await runner.test('Forward - Multiple destinations', async () => {
    const message = createTestMessage();
    
    await message.forward('dest1@test.com');
    await message.forward('dest2@test.com');
    
    const state = message.getState();
    assert.strictEqual(state.forwardDestinations.length, 2);
    assert.strictEqual(state.forwardDestinations[0].destination, 'dest1@test.com');
    assert.strictEqual(state.forwardDestinations[1].destination, 'dest2@test.com');
  });

  await runner.test('Forward - Invalid email address', async () => {
    const message = createTestMessage();
    
    await assert.rejects(
      message.forward('invalid-email'),
      /Invalid destination email address/
    );
  });

  await runner.test('Forward - Empty destination', async () => {
    const message = createTestMessage();
    
    await assert.rejects(
      message.forward(''),
      /Invalid destination email address/
    );
  });

  await runner.test('Forward - Invalid header (non-X prefix)', async () => {
    const message = createTestMessage();
    const headers = new Headers({ 'Content-Type': 'text/html' });
    
    await assert.rejects(
      message.forward('dest@test.com', headers),
      /Invalid header: Content-Type. Only X-\* headers are allowed/
    );
  });

  await runner.test('Forward - After rejection should fail', async () => {
    const message = createTestMessage();
    message.setReject('Test rejection');
    
    await assert.rejects(
      message.forward('dest@test.com'),
      /Cannot forward a rejected message/
    );
  });

  // ========== SetReject Method Tests ==========

  await runner.test('SetReject - Basic functionality', async () => {
    const message = createTestMessage();
    
    message.setReject('Test rejection reason');
    
    const state = message.getState();
    assert.strictEqual(state.rejected, true);
    assert.strictEqual(state.rejectReason, 'Test rejection reason');
  });

  await runner.test('SetReject - After forward should fail', async () => {
    const message = createTestMessage();
    await message.forward('dest@test.com');
    
    assert.throws(() => {
      message.setReject('Should fail');
    }, /Cannot reject a message that has already been forwarded/);
  });

  await runner.test('SetReject - Multiple calls overwrite', async () => {
    const message = createTestMessage();
    
    message.setReject('First reason');
    message.setReject('Second reason');
    
    const state = message.getState();
    assert.strictEqual(state.rejectReason, 'Second reason');
  });

  // ========== Reply Method Tests ==========

  await runner.test('Reply - Basic functionality', async () => {
    const message = createTestMessage();
    const replyMsg = new EmailMessage('reply@test.com', 'original@test.com');
    
    await message.reply(replyMsg);
    
    const state = message.getState();
    assert.strictEqual(state.replies.length, 1);
    assert.strictEqual(state.replies[0].from, 'reply@test.com');
    assert.strictEqual(state.replies[0].to, 'original@test.com');
  });

  await runner.test('Reply - Multiple replies', async () => {
    const message = createTestMessage();
    const reply1 = new EmailMessage('reply1@test.com', 'orig@test.com');
    const reply2 = new EmailMessage('reply2@test.com', 'orig@test.com');
    
    await message.reply(reply1);
    await message.reply(reply2);
    
    const state = message.getState();
    assert.strictEqual(state.replies.length, 2);
  });

  await runner.test('Reply - Invalid message object', async () => {
    const message = createTestMessage();
    
    await assert.rejects(
      message.reply(null),
      /Reply message must be an EmailMessage object/
    );
  });

  await runner.test('Reply - Missing from/to properties', async () => {
    const message = createTestMessage();
    const invalidReply = { from: 'test@test.com' }; // missing 'to'
    
    await assert.rejects(
      message.reply(invalidReply),
      /Reply message must have from and to properties/
    );
  });

  await runner.test('Reply - Invalid email addresses', async () => {
    const message = createTestMessage();
    const invalidReply = new EmailMessage('invalid-email', 'also-invalid');
    
    await assert.rejects(
      message.reply(invalidReply),
      /Invalid email addresses in reply message/
    );
  });

  await runner.test('Reply - After rejection should fail', async () => {
    const message = createTestMessage();
    message.setReject('Test rejection');
    const replyMsg = new EmailMessage('reply@test.com', 'orig@test.com');
    
    await assert.rejects(
      message.reply(replyMsg),
      /Cannot reply to a rejected message/
    );
  });

  // ========== State Management Tests ==========

  await runner.test('GetState - Initial state', async () => {
    const message = createTestMessage();
    const state = message.getState();
    
    assert.strictEqual(state.rejected, false);
    assert.strictEqual(state.forwarded, false);
    assert.strictEqual(state.forwardDestinations.length, 0);
    assert.strictEqual(state.replies.length, 0);
    assert(typeof state.headerCount === 'number');
    assert(state.headerCount > 0);
  });

  await runner.test('GetState - After operations', async () => {
    const message = createTestMessage();
    
    await message.forward('dest@test.com');
    const reply = new EmailMessage('reply@test.com', 'orig@test.com');
    await message.reply(reply);
    
    const state = message.getState();
    assert.strictEqual(state.forwarded, true);
    assert.strictEqual(state.forwardDestinations.length, 1);
    assert.strictEqual(state.replies.length, 1);
  });

  await runner.test('Reset - Clears all state', async () => {
    const message = createTestMessage();
    
    // Perform operations
    await message.forward('dest@test.com');
    const reply = new EmailMessage('reply@test.com', 'orig@test.com');
    await message.reply(reply);
    
    // Reset
    message.reset();
    
    const state = message.getState();
    assert.strictEqual(state.rejected, false);
    assert.strictEqual(state.forwarded, false);
    assert.strictEqual(state.forwardDestinations.length, 0);
    assert.strictEqual(state.replies.length, 0);
  });

  await runner.test('Reset - After rejection', async () => {
    const message = createTestMessage();
    
    message.setReject('Test rejection');
    message.reset();
    
    const state = message.getState();
    assert.strictEqual(state.rejected, false);
    assert.strictEqual(state.rejectReason, null);
    
    // Should be able to forward after reset
    await message.forward('dest@test.com');
    assert.strictEqual(message.getState().forwarded, true);
  });

  // ========== EmailMessage Class Tests ==========

  await runner.test('EmailMessage - Constructor validation', async () => {
    assert.throws(() => {
      new EmailMessage();
    }, /EmailMessage requires from and to addresses/);
    
    assert.throws(() => {
      new EmailMessage('from@test.com');
    }, /EmailMessage requires from and to addresses/);
  });

  await runner.test('EmailMessage - With options', async () => {
    const email = new EmailMessage('from@test.com', 'to@test.com', {
      subject: 'Test Subject',
      content: 'Test Content',
      headers: { 'X-Custom': 'value' }
    });
    
    assert.strictEqual(email.subject, 'Test Subject');
    assert.strictEqual(email.content, 'Test Content');
    assert.strictEqual(email.headers['X-Custom'], 'value');
  });

  // ========== Factory Function Tests ==========

  await runner.test('createMockEmailMessage - Default values', async () => {
    const message = createMockEmailMessage();
    
    assert.strictEqual(message.from, 'sender@example.com');
    assert.strictEqual(message.to, 'recipient@example.com');
    assert(message.headers.get('Subject').includes('Test Message'));
  });

  await runner.test('createMockEmailMessage - Custom options', async () => {
    const message = createMockEmailMessage({
      from: 'custom@test.com',
      to: 'dest@test.com',
      subject: 'Custom Subject',
      content: 'Custom content',
      headers: { 'X-Custom': 'custom-value' }
    });
    
    assert.strictEqual(message.from, 'custom@test.com');
    assert.strictEqual(message.to, 'dest@test.com');
    assert.strictEqual(message.headers.get('Subject'), 'Custom Subject');
    assert.strictEqual(message.headers.get('X-Custom'), 'custom-value');
  });

  // ========== Worker Interface Compatibility Tests ==========

  await runner.test('Worker Interface - Required properties exist', async () => {
    const message = createTestMessage();
    
    // Check all required properties for Cloudflare Worker compatibility
    assert(typeof message.from === 'string');
    assert(typeof message.to === 'string');
    assert(message.headers instanceof Headers);
    assert(typeof message.rawSize === 'number');
    assert(typeof message.raw === 'function');
    assert(typeof message.forward === 'function');
    assert(typeof message.setReject === 'function');
    assert(typeof message.reply === 'function');
  });

  await runner.test('Worker Interface - Raw as ReadableStream property', async () => {
    const message = createTestMessage();
    
    // Should work as ReadableStream property
    assert(typeof message.raw.getReader === 'function');
    assert(typeof message.raw.locked === 'boolean');
    assert(typeof message.raw.cancel === 'function');
  });

  await runner.test('Worker Interface - Headers enumeration', async () => {
    const message = createTestMessage();
    
    // Headers should be enumerable (used by existing Worker)
    let count = 0;
    for (const [key, value] of message.headers.entries()) {
      count++;
      assert(typeof key === 'string');
      assert(typeof value === 'string');
    }
    assert(count > 0);
  });

  await runner.test('Worker Interface - Async method behavior', async () => {
    const message = createTestMessage();
    
    // All async methods should return Promises
    const forwardPromise = message.forward('dest@test.com');
    assert(forwardPromise instanceof Promise);
    await forwardPromise;
    
    const reply = new EmailMessage('reply@test.com', 'orig@test.com');
    const replyPromise = message.reply(reply);
    assert(replyPromise instanceof Promise);
    await replyPromise;
  });

  // ========== Edge Cases and Error Handling ==========

  await runner.test('Edge Case - Empty string content', async () => {
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', '');
    
    assert.strictEqual(message.rawSize, 0);
    const raw = await message.raw();
    assert.strictEqual(raw.byteLength, 0);
  });

  await runner.test('Edge Case - Large content handling', async () => {
    const largeContent = 'x'.repeat(10000);
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', largeContent);
    
    assert.strictEqual(message.rawSize, 10000);
    const raw = await message.raw();
    assert.strictEqual(raw.byteLength, 10000);
  });

  await runner.test('Edge Case - Unicode content', async () => {
    const unicodeContent = '测试内容 🚀 émojis';
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', unicodeContent);
    
    const raw = await message.raw();
    const decoded = new TextDecoder().decode(raw);
    assert(decoded.includes(unicodeContent));
  });

  await runner.test('Edge Case - Headers case sensitivity', async () => {
    const headers = new Headers({ 'x-custom-header': 'value' });
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', 'content', headers);
    
    // Headers should normalize case
    assert(message.headers.get('X-Custom-Header') === 'value' || message.headers.get('x-custom-header') === 'value');
  });

  await runner.test('Error Handling - Concurrent stream reads', async () => {
    const content = 'Stream content';
    const stream = createReadableStream(content);
    const message = new ForwardableEmailMessage('from@test.com', 'to@test.com', stream);
    
    // First read should succeed
    const raw1 = await message.raw();
    assert(raw1 instanceof ArrayBuffer);
    
    // Second read should also succeed (uses cached content)
    const raw2 = await message.raw();
    assert.deepStrictEqual(new Uint8Array(raw1), new Uint8Array(raw2));
  });

  // ========== Performance and Memory Tests ==========

  await runner.test('Performance - State isolation', async () => {
    const message1 = createTestMessage();
    const message2 = createTestMessage();
    
    await message1.forward('dest1@test.com');
    message2.setReject('Test rejection');
    
    const state1 = message1.getState();
    const state2 = message2.getState();
    
    assert.strictEqual(state1.forwarded, true);
    assert.strictEqual(state1.rejected, false);
    assert.strictEqual(state2.forwarded, false);
    assert.strictEqual(state2.rejected, true);
  });

  return runner.summary();
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runComprehensiveTests()
    .then(success => {
      console.log(success ? '\n🎉 All tests passed!' : '\n💥 Some tests failed!');
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('❌ Test runner failed:', error);
      process.exit(1);
    });
}

export { runComprehensiveTests };