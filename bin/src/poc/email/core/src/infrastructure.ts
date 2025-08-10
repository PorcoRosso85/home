// External connections - Port/Adapter interfaces for dependency inversion

import { InvitationLink } from "./domain";

// Repository ports - for data persistence
export interface InvitationLinkRepository {
  save(invitationLink: InvitationLink): Promise<void>;
  findById(id: string): Promise<InvitationLink | null>;
  findByCampaignId(campaignId: string): Promise<InvitationLink[]>;
}

// Service ports - for external services  
export interface EmailService {
  sendInvitation(to: string, invitationLink: InvitationLink): Promise<void>;
}

export interface IdGenerator {
  generate(): string;
}

export interface UrlBuilder {
  buildInvitationUrl(inviterId: string, campaignId: string, id: string): string;
}