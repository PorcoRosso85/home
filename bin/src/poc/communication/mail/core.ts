/**
 * メール機能のコアビジネスロジック
 * Domain層：純粋関数で実装
 */

import type { Email, Draft, Account } from "./types.ts";

/**
 * メールの件名から返信用の件名を生成
 */
export function createReplySubject(originalSubject: string): string {
  if (originalSubject.startsWith("Re: ")) {
    return originalSubject;
  }
  return `Re: ${originalSubject}`;
}

/**
 * アカウントのバリデーション
 */
export function validateAccount(account: Partial<Account>): string[] {
  const errors: string[] = [];
  
  if (!account.email) {
    errors.push("メールアドレスは必須です");
  } else if (!isValidEmail(account.email)) {
    errors.push("有効なメールアドレスを入力してください");
  }
  
  if (!account.provider) {
    errors.push("プロバイダーは必須です");
  }
  
  if (!account.authType) {
    errors.push("認証タイプは必須です");
  }
  
  return errors;
}

/**
 * メールアドレスの簡易バリデーション
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 下書きのバリデーション
 */
export function validateDraft(draft: Partial<Draft>): string[] {
  const errors: string[] = [];
  
  if (!draft.toAddresses || draft.toAddresses.length === 0) {
    errors.push("宛先は必須です");
  } else {
    const invalidEmails = draft.toAddresses.filter(email => !isValidEmail(email));
    if (invalidEmails.length > 0) {
      errors.push(`無効なメールアドレス: ${invalidEmails.join(", ")}`);
    }
  }
  
  if (draft.ccAddresses) {
    const invalidCc = draft.ccAddresses.filter(email => !isValidEmail(email));
    if (invalidCc.length > 0) {
      errors.push(`無効なCCアドレス: ${invalidCc.join(", ")}`);
    }
  }
  
  return errors;
}

/**
 * メールをフィルタリング
 */
export function filterEmails(
  emails: Email[],
  options: {
    unreadOnly?: boolean;
    since?: Date;
  }
): Email[] {
  let filtered = emails;
  
  if (options.unreadOnly) {
    filtered = filtered.filter(email => !email.isRead);
  }
  
  if (options.since) {
    filtered = filtered.filter(email => email.receivedAt >= options.since);
  }
  
  return filtered;
}

/**
 * 返信用の下書きを作成
 */
export function createReplyDraft(
  originalEmail: Email,
  accountEmail: string
): Partial<Draft> {
  return {
    replyToEmailId: originalEmail.id,
    subject: createReplySubject(originalEmail.subject),
    toAddresses: [originalEmail.fromAddress],
    body: formatReplyBody(originalEmail, accountEmail)
  };
}

/**
 * 返信本文のフォーマット
 */
function formatReplyBody(originalEmail: Email, accountEmail: string): string {
  const date = originalEmail.receivedAt.toLocaleString("ja-JP");
  return `

-------- Original Message --------
From: ${originalEmail.fromAddress}
Date: ${date}
Subject: ${originalEmail.subject}

${originalEmail.bodyText || ""}`;
}