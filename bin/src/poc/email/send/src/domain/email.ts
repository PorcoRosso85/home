/**
 * Email domain model with validation
 */

export type Email = {
  readonly to: string;
  readonly subject: string;
  readonly body: string;
  readonly from?: string;
  readonly cc?: string;
  readonly bcc?: string;
  readonly replyTo?: string;
}

export type EmailInput = {
  to: string;
  subject: string;
  body: string;
  from?: string;
  cc?: string;
  bcc?: string;
  replyTo?: string;
}

export type CreateEmailResult = 
  | { success: true; email: Email }
  | { success: false; error: string };

/**
 * Validates if a string is a valid email format
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validates required fields are present and non-empty
 */
function validateRequiredField(value: string | undefined, fieldName: string): string | null {
  if (value === undefined || value === null) {
    return `${fieldName} is required`;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return `${fieldName} is required`;
  }
  return null;
}

/**
 * Validates optional email fields
 */
function validateOptionalEmailField(email: string | undefined, fieldName: string): string | null {
  if (email !== undefined && email !== null && !isValidEmail(email)) {
    return `Invalid email format for ${fieldName}`;
  }
  return null;
}

/**
 * Factory function to create and validate Email objects
 */
export function createEmail(input: EmailInput): CreateEmailResult {
  // Validate required fields
  const toError = validateRequiredField(input.to, 'to');
  if (toError) {
    return { success: false, error: toError };
  }

  const subjectError = validateRequiredField(input.subject, 'subject');
  if (subjectError) {
    return { success: false, error: subjectError };
  }

  const bodyError = validateRequiredField(input.body, 'body');
  if (bodyError) {
    return { success: false, error: bodyError };
  }

  // Validate email formats
  if (!isValidEmail(input.to)) {
    return { success: false, error: 'Invalid email format for to' };
  }

  const fromError = validateOptionalEmailField(input.from, 'from');
  if (fromError) {
    return { success: false, error: fromError };
  }

  const ccError = validateOptionalEmailField(input.cc, 'cc');
  if (ccError) {
    return { success: false, error: ccError };
  }

  const bccError = validateOptionalEmailField(input.bcc, 'bcc');
  if (bccError) {
    return { success: false, error: bccError };
  }

  const replyToError = validateOptionalEmailField(input.replyTo, 'replyTo');
  if (replyToError) {
    return { success: false, error: replyToError };
  }

  // Create the email object
  const email: Email = {
    to: input.to.trim(),
    subject: input.subject.trim(),
    body: input.body.trim(),
    ...(input.from && { from: input.from.trim() }),
    ...(input.cc && { cc: input.cc.trim() }),
    ...(input.bcc && { bcc: input.bcc.trim() }),
    ...(input.replyTo && { replyTo: input.replyTo.trim() })
  };

  return { success: true, email };
}