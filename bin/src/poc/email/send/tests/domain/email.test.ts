import { describe, test, expect } from "bun:test";
import { createEmail, type Email, type EmailInput } from "../../src/domain/email";

describe("Email Domain Model", () => {
  describe("createEmail", () => {
    test("should create valid email with required fields", () => {
      const emailData = {
        to: "recipient@example.com",
        subject: "Test Subject",
        body: "Test body content"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.email.to).toBe("recipient@example.com");
        expect(result.email.subject).toBe("Test Subject");
        expect(result.email.body).toBe("Test body content");
        expect(result.email.from).toBeUndefined();
        expect(result.email.cc).toBeUndefined();
        expect(result.email.bcc).toBeUndefined();
        expect(result.email.replyTo).toBeUndefined();
      }
    });

    test("should create valid email with all optional fields", () => {
      const emailData = {
        to: "recipient@example.com",
        subject: "Test Subject",
        body: "Test body content",
        from: "sender@example.com",
        cc: "cc@example.com",
        bcc: "bcc@example.com",
        replyTo: "reply@example.com"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.email.to).toBe("recipient@example.com");
        expect(result.email.subject).toBe("Test Subject");
        expect(result.email.body).toBe("Test body content");
        expect(result.email.from).toBe("sender@example.com");
        expect(result.email.cc).toBe("cc@example.com");
        expect(result.email.bcc).toBe("bcc@example.com");
        expect(result.email.replyTo).toBe("reply@example.com");
      }
    });

    test("should fail for invalid email address format in 'to' field", () => {
      const emailData = {
        to: "invalid-email",
        subject: "Test Subject",
        body: "Test body content"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("Invalid email format");
      }
    });

    test("should fail for invalid email address format in 'from' field", () => {
      const emailData = {
        to: "recipient@example.com",
        from: "invalid-email",
        subject: "Test Subject",
        body: "Test body content"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("Invalid email format");
      }
    });

    test("should fail when 'to' field is missing", () => {
      const emailData = {
        subject: "Test Subject",
        body: "Test body content"
      } as Partial<EmailInput>;

      const result = createEmail(emailData as EmailInput);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("to is required");
      }
    });

    test("should fail when 'subject' field is missing", () => {
      const emailData = {
        to: "recipient@example.com",
        body: "Test body content"
      } as Partial<EmailInput>;

      const result = createEmail(emailData as EmailInput);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("subject is required");
      }
    });

    test("should fail when 'body' field is missing", () => {
      const emailData = {
        to: "recipient@example.com",
        subject: "Test Subject"
      } as Partial<EmailInput>;

      const result = createEmail(emailData as EmailInput);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("body is required");
      }
    });

    test("should fail when 'to' field is empty string", () => {
      const emailData = {
        to: "",
        subject: "Test Subject",
        body: "Test body content"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("to is required");
      }
    });

    test("should fail when 'subject' field is empty string", () => {
      const emailData = {
        to: "recipient@example.com",
        subject: "",
        body: "Test body content"
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("subject is required");
      }
    });

    test("should fail when 'body' field is empty string", () => {
      const emailData = {
        to: "recipient@example.com",
        subject: "Test Subject",
        body: ""
      };

      const result = createEmail(emailData);
      
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toContain("body is required");
      }
    });
  });
});