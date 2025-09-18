// Test for the public API
import { processRequest, type Request, type Result, type InvitationLink } from "../src/mod";

describe("Public API", () => {
  test("should generate invitation link successfully", () => {
    const request: Request = {
      action: "generate_link",
      inviterId: "user123",
      campaignId: "campaign456"
    };

    const result: Result<InvitationLink> = processRequest(request);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.inviterId).toBe("user123");
      expect(result.data.campaignId).toBe("campaign456");
      expect(result.data.id).toMatch(/^inv_\d+_[a-z0-9]+$/);
      expect(result.data.url).toContain("user123/campaign456");
      expect(result.data.createdAt).toBeInstanceOf(Date);
    }
  });

  test("should handle unknown action gracefully", () => {
    const request = {
      action: "unknown_action",
      someData: "test"
    } as any;

    const result = processRequest(request);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.message).toBe("Unknown action: unknown_action");
    }
  });
});