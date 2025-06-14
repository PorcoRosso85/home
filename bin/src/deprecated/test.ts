#!/usr/bin/env -S nix shell nixpkgs#deno --command deno test

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";

function add(a: number, b: number): number {
  return a + b;
}

Deno.test("success1", () => {
  console.log("success1 test passed");
  assertEquals(add(0, 1), 1);
});


Deno.test("failure2", () => {
  Deno.test("failure2 nested", () => {
    assertEquals(add(1, 1), 2);
  });
});
