// Public API exports
import { createInvitationLink, type InvitationLink } from "./domain";
import { createInvitationUseCase, type UseCaseResult } from "./application";
import type { 
  InvitationLinkRepository, 
  EmailService, 
  IdGenerator, 
  UrlBuilder 
} from "./infrastructure";
import { config, type EnvironmentConfig } from "./variables";

export type { 
  InvitationLink, 
  UseCaseResult,
  InvitationLinkRepository,
  EmailService,
  IdGenerator,
  UrlBuilder,
  EnvironmentConfig
};
export { createInvitationUseCase, config };

export type Result<T, E = Error> = 
  | { ok: true; data: T }
  | { ok: false; error: E };

export interface GenerateLinkRequest {
  action: "generate_link";
  inviterId: string;
  campaignId: string;
}

export type Request = GenerateLinkRequest;

export function processRequest(request: Request): Result<InvitationLink> {
  try {
    switch (request.action) {
      case "generate_link":
        const link = createInvitationLink({
          inviterId: request.inviterId,
          campaignId: request.campaignId
        });
        return { ok: true, data: link };
      default:
        return { 
          ok: false, 
          error: new Error(`Unknown action: ${(request as any).action}`)
        };
    }
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error : new Error("Unknown error")
    };
  }
}