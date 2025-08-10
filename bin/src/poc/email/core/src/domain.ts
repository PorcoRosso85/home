// Business logic

import { config } from './variables.js';

export interface InvitationLink {
  id: string;
  inviterId: string;
  campaignId: string;
  url: string;
  createdAt: Date;
}

export interface CreateInvitationLinkParams {
  inviterId: string;
  campaignId: string;
}

export function createInvitationLink(params: CreateInvitationLinkParams): InvitationLink {
  const id = generateUniqueId();
  return {
    id,
    inviterId: params.inviterId,
    campaignId: params.campaignId,
    url: `${config.inviteBaseUrl}/${params.inviterId}/${params.campaignId}/${id}`,
    createdAt: new Date()
  };
}

function generateUniqueId(): string {
  return `inv_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export {};