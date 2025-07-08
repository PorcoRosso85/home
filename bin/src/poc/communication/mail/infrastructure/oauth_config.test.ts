import { assertEquals, assertThrows } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { loadProviderConfig, OAUTH2_PROVIDERS } from "./oauth_config.ts";

Deno.test("OAuth2 Provider Config", async (t) => {
  await t.step("should have Gmail provider", () => {
    const gmail = OAUTH2_PROVIDERS.gmail;
    assertEquals(gmail.name, "Gmail");
    assertEquals(gmail.authUrl, "https://accounts.google.com/o/oauth2/v2/auth");
    assertEquals(gmail.tokenUrl, "https://oauth2.googleapis.com/token");
    assertEquals(gmail.scopes.length > 0, true);
  });

  await t.step("should have Outlook provider", () => {
    const outlook = OAUTH2_PROVIDERS.outlook;
    assertEquals(outlook.name, "Outlook");
    assertEquals(outlook.authUrl.includes("microsoftonline.com"), true);
  });

  await t.step("should load provider config with CLI args", () => {
    const config = loadProviderConfig("gmail", "test-id", "test-secret");
    assertEquals(config.clientId, "test-id");
    assertEquals(config.clientSecret, "test-secret");
    assertEquals(config.provider.name, "Gmail");
  });

  await t.step("should load provider config from env vars", () => {
    // 環境変数を設定
    Deno.env.set("GMAIL_CLIENT_ID", "env-id");
    Deno.env.set("GMAIL_CLIENT_SECRET", "env-secret");
    
    const config = loadProviderConfig("gmail");
    assertEquals(config.clientId, "env-id");
    assertEquals(config.clientSecret, "env-secret");
    
    // クリーンアップ
    Deno.env.delete("GMAIL_CLIENT_ID");
    Deno.env.delete("GMAIL_CLIENT_SECRET");
  });

  await t.step("should prefer CLI args over env vars", () => {
    // 環境変数を設定
    Deno.env.set("GMAIL_CLIENT_ID", "env-id");
    Deno.env.set("GMAIL_CLIENT_SECRET", "env-secret");
    
    const config = loadProviderConfig("gmail", "cli-id", "cli-secret");
    assertEquals(config.clientId, "cli-id");
    assertEquals(config.clientSecret, "cli-secret");
    
    // クリーンアップ
    Deno.env.delete("GMAIL_CLIENT_ID");
    Deno.env.delete("GMAIL_CLIENT_SECRET");
  });

  await t.step("should throw for unknown provider", () => {
    assertThrows(
      () => loadProviderConfig("unknown", "id", "secret"),
      Error,
      "Unknown provider"
    );
  });

  await t.step("should throw when credentials missing", () => {
    assertThrows(
      () => loadProviderConfig("gmail"),
      Error,
      "Missing OAuth2 credentials"
    );
  });
});