import { resolveKiroDir, type KiroDirOptions } from '../resolvers/kiroDir.js';
import { resolveAgentLayout, type AgentType, type CCSddConfig } from '../resolvers/agentLayout.js';

export interface BuildTemplateContextOptions {
  agent: AgentType;
  lang: 'ja' | 'en' | 'zh-TW';
  kiroDir?: KiroDirOptions;
  config?: CCSddConfig;
}

export type TemplateContext = {
  LANG_CODE: string;
  KIRO_DIR: string;
  AGENT_DIR: string;
  AGENT_DOC: string;
  AGENT_COMMANDS_DIR: string;
};


export const buildTemplateContext = (opts: BuildTemplateContextOptions): TemplateContext => {
  const kiro = resolveKiroDir(opts.kiroDir ?? {});
  const layout = resolveAgentLayout(opts.agent, opts.config);
  return {
    LANG_CODE: opts.lang,
    KIRO_DIR: kiro,
    AGENT_DIR: layout.agentDir,
    AGENT_DOC: layout.docFile,
    AGENT_COMMANDS_DIR: layout.commandsDir,
  };
};
