import { test, expect } from "bun:test";
import { existsSync } from "fs";
import packageJson from "../package.json";

test("project initialization verification", () => {
  // Verify package.json exists and has correct name
  expect(packageJson.name).toBe("x-api-poc");
  expect(packageJson.type).toBe("module");
  
  // Verify TypeScript configuration exists
  expect(existsSync("tsconfig.json")).toBe(true);
  
  // Verify main entry point exists
  expect(existsSync("index.ts")).toBe(true);
  
  // Verify environment example file exists
  expect(existsSync(".env.example")).toBe(true);
});

test("TypeScript configuration", async () => {
  const tsConfigText = await Bun.file("tsconfig.json").text();
  
  // Verify tsconfig.json contains required configurations
  expect(tsConfigText).toContain("ESNext");
  expect(tsConfigText).toContain("compilerOptions");
  expect(tsConfigText).toContain("strict");
});

test("package.json dependencies", () => {
  // Verify development dependencies are present
  expect(packageJson.devDependencies).toBeDefined();
  expect(packageJson.devDependencies["@types/bun"]).toBeTruthy();
  
  // Verify TypeScript peer dependency
  expect(packageJson.peerDependencies).toBeDefined();
  expect(packageJson.peerDependencies["typescript"]).toBeTruthy();
});