import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";

Deno.test({
  name: "File read permission - should fail without permission",
  permissions: {
    read: false,
  },
  async fn() {
    await assertRejects(
      async () => {
        await Deno.readTextFile("/etc/passwd");
      },
      Deno.errors.PermissionDenied,
      "Requires read access"
    );
  },
});

Deno.test({
  name: "File read permission - should succeed with specific path permission",
  permissions: {
    read: ["./src"],
  },
  async fn() {
    const content = await Deno.readTextFile("./src/file_access.ts");
    assertEquals(content.includes("File Access Demo"), true);
  },
});

Deno.test({
  name: "Network permission - should fail without permission",
  permissions: {
    net: false,
  },
  async fn() {
    await assertRejects(
      async () => {
        await fetch("https://api.github.com");
      },
      Deno.errors.PermissionDenied,
      "Requires net access"
    );
  },
});

Deno.test({
  name: "Network permission - should succeed with specific domain permission",
  permissions: {
    net: ["api.github.com"],
  },
  async fn() {
    const response = await fetch("https://api.github.com");
    assertEquals(response.ok, true);
  },
});

Deno.test({
  name: "Environment permission - should fail without permission",
  permissions: {
    env: false,
  },
  fn() {
    try {
      Deno.env.get("HOME");
      throw new Error("Should have thrown PermissionDenied");
    } catch (error) {
      assertEquals(error instanceof Deno.errors.PermissionDenied, true);
    }
  },
});

Deno.test({
  name: "Environment permission - should succeed with specific var permission",
  permissions: {
    env: ["HOME"],
  },
  fn() {
    const home = Deno.env.get("HOME");
    assertEquals(typeof home, "string");
  },
});

Deno.test({
  name: "Run permission - should fail without permission",
  permissions: {
    run: false,
  },
  async fn() {
    await assertRejects(
      async () => {
        const command = new Deno.Command("echo", {
          args: ["Hello"],
        });
        await command.output();
      },
      Deno.errors.PermissionDenied,
      "Requires run access"
    );
  },
});

Deno.test({
  name: "Run permission - should succeed with specific command permission",
  permissions: {
    run: ["echo"],
  },
  async fn() {
    const command = new Deno.Command("echo", {
      args: ["Hello", "World"],
    });
    const { code } = await command.output();
    assertEquals(code, 0);
  },
});

Deno.test({
  name: "Multiple permissions - combined restrictions work correctly",
  permissions: {
    read: ["./src"],
    net: false,
    env: ["USER"],
    run: false,
  },
  async fn() {
    const content = await Deno.readTextFile("./src/file_access.ts");
    assertEquals(content.includes("File Access Demo"), true);

    await assertRejects(
      async () => {
        await fetch("https://api.github.com");
      },
      Deno.errors.PermissionDenied
    );

    const user = Deno.env.get("USER");
    assertEquals(typeof user, "string");

    try {
      Deno.env.get("PATH");
      throw new Error("Should have thrown PermissionDenied");
    } catch (error) {
      assertEquals(error instanceof Deno.errors.PermissionDenied, true);
    }
  },
});