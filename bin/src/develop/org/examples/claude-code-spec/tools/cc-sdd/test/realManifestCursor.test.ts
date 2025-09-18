import { describe, it, expect } from 'vitest';
import { runCli } from '../src/index';
import { join } from 'node:path';

const runtime = { platform: 'darwin' } as const;

const makeIO = () => {
  const logs: string[] = [];
  const errs: string[] = [];
  return {
    io: {
      log: (m: string) => logs.push(m),
      error: (m: string) => errs.push(m),
      exit: (_c: number) => {},
    },
    get logs() {
      return logs;
    },
    get errs() {
      return errs;
    },
  };
};

describe('real cursor manifest', () => {
  it('dry-run prints plan for cursor.json with placeholders applied (mac)', async () => {
    const repoRoot = join(process.cwd(), '..', '..');
    const manifestPath = join(repoRoot, 'tools/cc-sdd/templates/manifests/cursor.json');
    const ctx = makeIO();
    const code = await runCli(['--dry-run', '--lang', 'en', '--agent', 'cursor', '--manifest', manifestPath], runtime, ctx.io, {});
    expect(code).toBe(0);
    const out = ctx.logs.join('\n');
    expect(out).toMatch(/Plan \(dry-run\)/);
    expect(out).toContain('[templateDir] commands_all_os: templates/agents/cursor/commands/os-mac -> .cursor/commands/kiro');
    expect(out).toContain('[templateFile] doc_main: templates/agents/cursor/docs/AGENTS/AGENTS.en.tpl.md -> ./AGENTS.md');
  });
  it('dry-run prints plan including commands for linux via mac template', async () => {
    const repoRoot = join(process.cwd(), '..', '..');
    const manifestPath = join(repoRoot, 'tools/cc-sdd/templates/manifests/cursor.json');
    const ctx = makeIO();
    const runtimeLinux = { platform: 'linux' } as const;
    const code = await runCli(['--dry-run', '--lang', 'en', '--agent', 'cursor', '--manifest', manifestPath], runtimeLinux, ctx.io, {});
    expect(code).toBe(0);
    const out = ctx.logs.join('\n');
    expect(out).toMatch(/Plan \(dry-run\)/);
    expect(out).toContain('[templateDir] commands_all_os: templates/agents/cursor/commands/os-mac -> .cursor/commands/kiro');
    expect(out).toContain('[templateFile] doc_main: templates/agents/cursor/docs/AGENTS/AGENTS.en.tpl.md -> ./AGENTS.md');
  });
});
