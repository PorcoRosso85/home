import { describe, test, expect } from "bun:test";
import { createInvitationLink } from "../src/domain";

describe("InvitationLink Domain", () => {
  test("should create invitation link with unique ID", () => {
    const link = createInvitationLink({
      inviterId: "user123",
      campaignId: "camp456"
    });
    
    expect(link.id).toBeDefined();
    expect(link.inviterId).toBe("user123");
    expect(link.campaignId).toBe("camp456");
    expect(link.url).toContain("user123");
  });
  
  test("should generate different IDs for different links", () => {
    const link1 = createInvitationLink({
      inviterId: "user123",
      campaignId: "camp456"
    });
    const link2 = createInvitationLink({
      inviterId: "user123",
      campaignId: "camp456"
    });
    
    expect(link1.id).not.toBe(link2.id);
  });
});