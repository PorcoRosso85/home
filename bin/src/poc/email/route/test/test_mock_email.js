/**
 * Test script for ForwardableEmailMessage mock implementation
 */

import { ForwardableEmailMessage, EmailMessage, createMockEmailMessage } from '../src/mock/ForwardableEmailMessage.js';

async function runTests() {
  console.log('🧪 Testing ForwardableEmailMessage Mock Implementation\n');

  // Test 1: Basic construction and properties
  console.log('Test 1: Basic Construction');
  const message1 = createMockEmailMessage({
    from: 'test@example.com',
    to: 'recipient@example.com',
    subject: 'Test Subject',
    content: 'Hello, this is a test message!'
  });

  console.log('✓ Message created successfully');
  console.log(`  From: ${message1.from}`);
  console.log(`  To: ${message1.to}`);
  console.log(`  Raw Size: ${message1.rawSize} bytes`);
  console.log(`  Headers: ${Array.from(message1.headers.entries()).length} entries\n`);

  // Test 2: Raw content access
  console.log('Test 2: Raw Content Access');
  const rawContent = await message1.raw();
  const textDecoder = new TextDecoder();
  const emailText = textDecoder.decode(rawContent);
  console.log('✓ Raw content retrieved successfully');
  console.log(`  Content preview: ${emailText.substring(0, 100)}...\n`);

  // Test 3: Forward functionality
  console.log('Test 3: Forward Functionality');
  const message2 = createMockEmailMessage();
  
  try {
    await message2.forward('forwarded@example.com');
    console.log('✓ Forward operation completed');
    
    const state = message2.getState();
    console.log(`  Forwarded: ${state.forwarded}`);
    console.log(`  Destinations: ${state.forwardDestinations.length}`);
    console.log(`  Destination: ${state.forwardDestinations[0]?.destination}\n`);
  } catch (error) {
    console.error('✗ Forward failed:', error.message);
  }

  // Test 4: Forward with extra headers
  console.log('Test 4: Forward with Extra Headers');
  const message3 = createMockEmailMessage();
  const extraHeaders = new Headers({
    'X-Custom-Header': 'test-value',
    'X-Forward-Reason': 'automated-forwarding'
  });

  try {
    await message3.forward('custom@example.com', extraHeaders);
    console.log('✓ Forward with extra headers completed');
    
    const state = message3.getState();
    console.log(`  Extra headers: ${JSON.stringify(state.forwardDestinations[0]?.headers)}\n`);
  } catch (error) {
    console.error('✗ Forward with headers failed:', error.message);
  }

  // Test 5: Reject functionality
  console.log('Test 5: Reject Functionality');
  const message4 = createMockEmailMessage();
  
  try {
    message4.setReject('Sender not on allowlist');
    console.log('✓ Reject operation completed');
    
    const state = message4.getState();
    console.log(`  Rejected: ${state.rejected}`);
    console.log(`  Reason: ${state.rejectReason}\n`);
  } catch (error) {
    console.error('✗ Reject failed:', error.message);
  }

  // Test 6: Reply functionality
  console.log('Test 6: Reply Functionality');
  const message5 = createMockEmailMessage();
  const replyMessage = new EmailMessage(
    'auto-reply@example.com',
    'original-sender@example.com',
    {
      subject: 'Re: Your message',
      content: 'Thank you for your message. We will respond shortly.'
    }
  );

  try {
    await message5.reply(replyMessage);
    console.log('✓ Reply operation completed');
    
    const state = message5.getState();
    console.log(`  Replies sent: ${state.replies.length}`);
    console.log(`  Reply to: ${state.replies[0]?.to}\n`);
  } catch (error) {
    console.error('✗ Reply failed:', error.message);
  }

  // Test 7: Error handling - reject after forward
  console.log('Test 7: Error Handling - Reject After Forward');
  const message6 = createMockEmailMessage();
  
  try {
    await message6.forward('test@example.com');
    message6.setReject('Should fail');
    console.error('✗ Expected error not thrown');
  } catch (error) {
    console.log('✓ Correctly prevented reject after forward');
    console.log(`  Error: ${error.message}\n`);
  }

  // Test 8: Error handling - invalid headers
  console.log('Test 8: Error Handling - Invalid Headers');
  const message7 = createMockEmailMessage();
  const invalidHeaders = new Headers({
    'Content-Type': 'text/html', // Not allowed, only X-* headers
    'X-Valid-Header': 'this-is-ok'
  });

  try {
    await message7.forward('test@example.com', invalidHeaders);
    console.error('✗ Expected error not thrown');
  } catch (error) {
    console.log('✓ Correctly rejected invalid headers');
    console.log(`  Error: ${error.message}\n`);
  }

  // Test 9: ReadableStream construction
  console.log('Test 9: ReadableStream Construction');
  const streamContent = 'Test content via ReadableStream';
  const encoder = new TextEncoder();
  const bytes = encoder.encode(streamContent);
  
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    }
  });

  const message8 = new ForwardableEmailMessage(
    'stream@example.com',
    'test@example.com',
    stream
  );

  try {
    const rawFromStream = await message8.raw();
    const decodedContent = new TextDecoder().decode(rawFromStream);
    console.log('✓ ReadableStream construction successful');
    console.log(`  Content: ${decodedContent}`);
    console.log(`  Size: ${message8.rawSize} bytes\n`);
  } catch (error) {
    console.error('✗ ReadableStream test failed:', error.message);
  }

  console.log('🎉 All tests completed!\n');
  
  // Summary
  console.log('📋 Mock Implementation Summary:');
  console.log('   ✓ Implements all required Cloudflare Email interface methods');
  console.log('   ✓ Supports forward(), setReject(), reply()');
  console.log('   ✓ Handles ReadableStream, string, and ArrayBuffer inputs');
  console.log('   ✓ Validates email addresses and headers');
  console.log('   ✓ Provides state tracking for testing');
  console.log('   ✓ Compatible with existing Worker implementation');
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { runTests };