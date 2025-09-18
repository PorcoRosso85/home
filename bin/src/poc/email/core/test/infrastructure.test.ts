import { describe, it, expect } from "bun:test";
import type { 
  InvitationLinkRepository, 
  EmailService, 
  IdGenerator, 
  UrlBuilder 
} from "../src/infrastructure";
import { InvitationLink } from "../src/domain";

describe("Infrastructure Interface Contracts", () => {
  describe("InvitationLinkRepository", () => {
    it("should have correct method signatures", () => {
      // Test that the interface exists and has expected shape
      const mockRepository: InvitationLinkRepository = {
        save: async (invitationLink: InvitationLink): Promise<void> => {},
        findById: async (id: string): Promise<InvitationLink | null> => null,
        findByCampaignId: async (campaignId: string): Promise<InvitationLink[]> => []
      };

      expect(typeof mockRepository.save).toBe("function");
      expect(typeof mockRepository.findById).toBe("function"); 
      expect(typeof mockRepository.findByCampaignId).toBe("function");
    });

    it("should accept InvitationLink for save method", async () => {
      const invitationLink: InvitationLink = {
        id: "inv_123",
        inviterId: "user_456",
        campaignId: "camp_789",
        url: "https://invite.example.com/user_456/camp_789/inv_123",
        createdAt: new Date()
      };

      const mockRepository: InvitationLinkRepository = {
        save: async (link: InvitationLink): Promise<void> => {
          expect(link.id).toBe("inv_123");
          expect(link.inviterId).toBe("user_456");
          expect(link.campaignId).toBe("camp_789");
        },
        findById: async (): Promise<InvitationLink | null> => null,
        findByCampaignId: async (): Promise<InvitationLink[]> => []
      };

      await mockRepository.save(invitationLink);
    });
  });

  describe("EmailService", () => {
    it("should have correct method signature", () => {
      const mockService: EmailService = {
        sendInvitation: async (to: string, invitationLink: InvitationLink): Promise<void> => {}
      };

      expect(typeof mockService.sendInvitation).toBe("function");
    });

    it("should accept email and InvitationLink parameters", async () => {
      const invitationLink: InvitationLink = {
        id: "inv_123",
        inviterId: "user_456", 
        campaignId: "camp_789",
        url: "https://invite.example.com/user_456/camp_789/inv_123",
        createdAt: new Date()
      };

      const mockService: EmailService = {
        sendInvitation: async (to: string, link: InvitationLink): Promise<void> => {
          expect(to).toBe("test@example.com");
          expect(link.id).toBe("inv_123");
        }
      };

      await mockService.sendInvitation("test@example.com", invitationLink);
    });
  });

  describe("IdGenerator", () => {
    it("should have correct method signature", () => {
      const mockGenerator: IdGenerator = {
        generate: (): string => "generated_id"
      };

      expect(typeof mockGenerator.generate).toBe("function");
      expect(typeof mockGenerator.generate()).toBe("string");
    });
  });

  describe("UrlBuilder", () => {
    it("should have correct method signature", () => {
      const mockBuilder: UrlBuilder = {
        buildInvitationUrl: (inviterId: string, campaignId: string, id: string): string => 
          `https://invite.example.com/${inviterId}/${campaignId}/${id}`
      };

      expect(typeof mockBuilder.buildInvitationUrl).toBe("function");
      
      const url = mockBuilder.buildInvitationUrl("user_123", "camp_456", "inv_789");
      expect(typeof url).toBe("string");
      expect(url).toContain("user_123");
      expect(url).toContain("camp_456"); 
      expect(url).toContain("inv_789");
    });
  });
});