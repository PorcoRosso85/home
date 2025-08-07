/**
 * Usage example demonstrating SendService integration with storage and sender
 */

import { createEmail } from '../domain/email.js';
import { InMemoryStorage } from '../adapters/storage/memory.js';
import { SendService } from '../application/send-service.js';

// Mock email sender for demonstration
class MockEmailSender {
  async send(email: any, options?: any) {
    if (options?.dryRun) {
      console.log('DRY RUN - Would send email:', email);
      return { success: true, messageId: 'dry-run-message-id' };
    }
    
    console.log('Sending email:', email);
    return { success: true, messageId: 'message-12345' };
  }
}

async function demonstrateUsage() {
  console.log('=== Email Send Service Demo ===\n');

  // Initialize components
  const storage = new InMemoryStorage();
  const emailSender = new MockEmailSender();
  const sendService = new SendService(storage, emailSender);

  // Create a sample email
  const emailResult = createEmail({
    to: 'recipient@example.com',
    subject: 'Hello from SendService',
    body: 'This is a test email sent through the SendService!',
    from: 'sender@example.com'
  });

  if (!emailResult.success) {
    console.error('Failed to create email:', emailResult.error);
    return;
  }

  const email = emailResult.email;
  console.log('1. Created email:', email);

  // Save email as draft
  const draftResult = await storage.saveDraft(email, 'demo-draft-001');
  if (!draftResult.success) {
    console.error('Failed to save draft:', draftResult.error);
    return;
  }

  const draftId = draftResult.data;
  console.log('2. Saved as draft with ID:', draftId);

  // Send the draft (dry run)
  console.log('\n3. Sending draft in dry run mode...');
  const dryRunResult = await sendService.sendDraft(draftId, { dryRun: true });
  console.log('Dry run result:', dryRunResult);

  // Send the draft for real
  console.log('\n4. Sending draft for real...');
  const sendResult = await sendService.sendDraft(draftId);
  console.log('Send result:', sendResult);

  // Try to send non-existent draft
  console.log('\n5. Attempting to send non-existent draft...');
  const errorResult = await sendService.sendDraft('non-existent-draft');
  console.log('Error result:', errorResult);

  console.log('\n=== Demo Complete ===');
}

// Export for potential usage
export { demonstrateUsage };

// Run demo if this file is executed directly
if (import.meta.main) {
  demonstrateUsage().catch(console.error);
}