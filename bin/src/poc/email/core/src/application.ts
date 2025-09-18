// Use cases
import { createInvitationLink, CreateInvitationLinkParams, InvitationLink } from "./domain";

export interface UseCaseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export function createInvitationUseCase(params: CreateInvitationLinkParams): UseCaseResult<InvitationLink> {
  // Application layer validation - use case specific concerns
  if (!params.inviterId || params.inviterId.trim() === "") {
    return {
      success: false,
      error: "Inviter ID is required"
    };
  }

  if (!params.campaignId || params.campaignId.trim() === "") {
    return {
      success: false,
      error: "Campaign ID is required"
    };
  }

  // Orchestrate domain logic
  try {
    const invitationLink = createInvitationLink(params);
    
    return {
      success: true,
      data: invitationLink
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error occurred"
    };
  }
}