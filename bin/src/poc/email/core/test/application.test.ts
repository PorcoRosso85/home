import { describe, test, expect } from "bun:test";
import { createInvitationUseCase } from "../src/application";

describe("Application Layer - Use Cases", () => {
  test("should create invitation link through use case", () => {
    const params = {
      inviterId: "user123",
      campaignId: "camp456"
    };
    
    const result = createInvitationUseCase(params);
    
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data?.id).toBeDefined();
    expect(result.data?.inviterId).toBe("user123");
    expect(result.data?.campaignId).toBe("camp456");
    expect(result.data?.url).toContain("user123");
    expect(result.data?.createdAt).toBeInstanceOf(Date);
  });

  test("should return error for invalid inviter ID", () => {
    const params = {
      inviterId: "",
      campaignId: "camp456"
    };
    
    const result = createInvitationUseCase(params);
    
    expect(result.success).toBe(false);
    expect(result.error).toBe("Inviter ID is required");
  });

  test("should return error for invalid campaign ID", () => {
    const params = {
      inviterId: "user123",
      campaignId: ""
    };
    
    const result = createInvitationUseCase(params);
    
    expect(result.success).toBe(false);
    expect(result.error).toBe("Campaign ID is required");
  });
});