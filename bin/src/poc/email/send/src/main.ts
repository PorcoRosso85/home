#!/usr/bin/env bun
/**
 * CLI Entry Point for Email Send Service
 * Provides dry run testing and real email sending capabilities
 */

import { createEmail, Email } from './domain/email.js';
import { InMemoryStorage } from './infrastructure/storage/memory.js';
import { createSESEmailSender } from './infrastructure/sender/ses.js';
import { SendService } from './application/send-service.js';
import { SendOptions, SendResult } from './domain/ports.js';

/**
 * Parse command line arguments
 */
function parseArgs(): { dryRun: boolean; help: boolean } {
  const args = process.argv.slice(2);
  return {
    dryRun: args.includes('--dry-run'),
    help: args.includes('--help') || args.includes('-h')
  };
}

/**
 * Display help message
 */
function showHelp(): void {
  console.log(`
Email Send Service CLI

USAGE:
  bun run src/main.ts [OPTIONS]

OPTIONS:
  --dry-run    Test email sending without actually sending (recommended for testing)
  --help, -h   Show this help message

EXAMPLES:
  # Test email sending without sending real emails
  bun run src/main.ts --dry-run

  # Send real emails (requires AWS SES configuration)
  bun run src/main.ts

ENVIRONMENT VARIABLES (required for real sending):
  AWS_REGION              AWS region (e.g., us-east-1)
  AWS_ACCESS_KEY_ID       AWS access key ID
  AWS_SECRET_ACCESS_KEY   AWS secret access key

SAMPLE OUTPUT:
  • Creates a sample email draft
  • Saves it to in-memory storage
  • Sends the draft with dry run support
  • Shows clear status messages and error handling

For dry run mode, no AWS credentials are required.
`);
}

/**
 * Get AWS SES configuration from environment variables
 */
function getSESConfig() {
  const region = process.env.AWS_REGION;
  const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;

  if (!region || !accessKeyId || !secretAccessKey) {
    return null;
  }

  return {
    region,
    credentials: {
      accessKeyId,
      secretAccessKey
    }
  };
}

/**
 * Create a sample email for demonstration
 */
function createSampleEmail() {
  return createEmail({
    to: 'recipient@example.com',
    from: 'sender@example.com',
    subject: 'Test Email from CLI',
    body: `This is a test email sent via the Email Send Service CLI.

Sent at: ${new Date().toISOString()}

This email demonstrates the dry run and real sending capabilities of the service.`
  });
}

/**
 * Mock email sender for dry run mode
 */
class MockEmailSender {
  async send(email: Email, options?: SendOptions): Promise<SendResult> {
    if (options?.dryRun) {
      console.log('🧪 DRY RUN - Email would be sent with the following details:');
      console.log('   To:', email.to);
      console.log('   From:', email.from || 'noreply@example.com');
      console.log('   Subject:', email.subject);
      console.log('   Body Preview:', email.body.substring(0, 100) + '...');
      
      const mockMessageId = `dry-run-${Math.random().toString(36).substring(2, 14)}`;
      return { success: true, messageId: mockMessageId };
    }
    
    throw new Error('MockEmailSender should only be used in dry run mode');
  }
}

/**
 * Main CLI function
 */
async function main(): Promise<void> {
  console.log('📧 Email Send Service CLI\n');

  const { dryRun, help } = parseArgs();

  if (help) {
    showHelp();
    return;
  }

  // Initialize storage
  console.log('🔧 Initializing in-memory storage...');
  const storage = new InMemoryStorage();

  // Initialize email sender based on mode
  let emailSender;
  let sesConfig;

  if (dryRun) {
    console.log('🧪 Running in DRY RUN mode - no real emails will be sent\n');
    emailSender = new MockEmailSender();
  } else {
    console.log('🚀 Running in REAL mode - emails will be sent via AWS SES');
    
    sesConfig = getSESConfig();
    if (!sesConfig) {
      console.error('❌ ERROR: AWS SES configuration missing!');
      console.error('   Required environment variables:');
      console.error('   - AWS_REGION');
      console.error('   - AWS_ACCESS_KEY_ID');
      console.error('   - AWS_SECRET_ACCESS_KEY\n');
      console.error('💡 TIP: Use --dry-run to test without AWS credentials');
      process.exit(1);
    }

    const senderResult = createSESEmailSender(sesConfig);
    
    if (!senderResult.success) {
      console.error('❌ ERROR: Failed to initialize AWS SES:', senderResult.error);
      process.exit(1);
    }
    
    emailSender = senderResult.sender;
    console.log('✅ AWS SES configuration loaded successfully\n');
  }

  // Initialize send service
  const sendService = new SendService(storage, emailSender);

  try {
    // Create sample email
    console.log('📝 Creating sample email...');
    const emailResult = createSampleEmail();
    
    if (!emailResult.success) {
      console.error('❌ Failed to create email:', emailResult.error);
      process.exit(1);
    }

    const email = emailResult.email;
    console.log('✅ Sample email created');
    console.log('   To:', email.to);
    console.log('   Subject:', email.subject);
    console.log('   Body length:', email.body.length, 'characters\n');

    // Save email as draft
    console.log('💾 Saving email as draft...');
    const draftId = 'cli-demo-draft-' + Date.now();
    const draftResult = await storage.saveDraft(email, draftId);
    
    if (!draftResult.success) {
      console.error('❌ Failed to save draft:', draftResult.error);
      process.exit(1);
    }

    console.log('✅ Email saved as draft with ID:', draftResult.data);
    console.log('');

    // Send the draft
    console.log(dryRun ? '🧪 Sending draft in DRY RUN mode...' : '📤 Sending draft via AWS SES...');
    const sendResult = await sendService.sendDraft(draftResult.data, { dryRun });
    
    if (sendResult.success) {
      console.log('✅ Email sent successfully!');
      console.log('   Message ID:', sendResult.messageId);
      
      if (dryRun) {
        console.log('\n💡 This was a dry run. No real email was sent.');
        console.log('   Run without --dry-run to send real emails (requires AWS SES setup)');
      } else {
        console.log('\n🎉 Real email sent via AWS SES!');
      }
    } else {
      console.error('❌ Failed to send email:', sendResult.error);
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Unexpected error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }

  console.log('\n✨ CLI execution completed successfully!');
}

// Handle uncaught errors gracefully
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught exception:', error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('❌ Unhandled promise rejection:', reason);
  process.exit(1);
});

// Run main function if this file is executed directly
if (import.meta.main) {
  main().catch((error) => {
    console.error('❌ CLI failed:', error instanceof Error ? error.message : error);
    process.exit(1);
  });
}