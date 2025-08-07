# Development Email Endpoint

This directory contains development utilities for testing the email archive worker locally.

## email-endpoint.js

Provides a `/__email` endpoint that accepts POST requests with email data and converts them to ForwardableEmailMessage format for testing the Worker's email handler.

### Usage

1. **Start the development server:**
   ```bash
   npm run dev:email
   ```
   This will start wrangler dev with the email endpoint available at `http://localhost:8787`

2. **Send test emails:**

   **Option A: JSON Format**
   ```bash
   curl -X POST http://localhost:8787/__email \
     -H "Content-Type: application/json" \
     -d '{
       "from": "test@example.com",
       "to": "archive@example.com", 
       "subject": "Test Email",
       "content": "This is a test email message.",
       "headers": {
         "X-Custom-Header": "test-value"
       }
     }'
   ```

   **Option B: Raw Email Format**
   ```bash
   curl -X POST http://localhost:8787/__email \
     -H "Content-Type: text/plain" \
     -d "From: test@example.com
   To: archive@example.com
   Subject: Test Email
   Date: $(date -R)
   Message-ID: <test-$(date +%s)@example.com>

   This is a test email message."
   ```

3. **Quick test using npm script:**
   ```bash
   npm run test:email-endpoint
   ```

### Available Endpoints

- `/__email` (POST) - Process email data
- `/__health` (GET) - Health check and endpoint documentation
- `/` (GET) - Usage information

### Email Data Format

When sending JSON data, use the following structure:

```json
{
  "from": "sender@example.com",      // Required
  "to": "recipient@example.com",     // Required  
  "subject": "Email Subject",        // Optional
  "content": "Email body content",   // Optional
  "headers": {                       // Optional
    "X-Custom": "value"
  },
  "raw": "raw email content"         // Optional - if provided, used instead of generating content
}
```

### Integration with Worker

The endpoint automatically:

1. Parses incoming email data (JSON or raw format)
2. Converts it to a ForwardableEmailMessage instance
3. Calls the Worker's `email()` handler function
4. Returns the processing result

This allows you to test the complete email processing pipeline locally without needing actual email routing setup.

### Testing with MinIO

Make sure your MinIO instance is running (see main README.md) before testing:

```bash
# Start MinIO (from project root)
./setup-minio.sh

# Start the email endpoint
npm run dev:email

# Send test email
npm run test:email-endpoint
```

The processed emails will be stored in your local MinIO instance at `http://localhost:9001` (MinIO Console).