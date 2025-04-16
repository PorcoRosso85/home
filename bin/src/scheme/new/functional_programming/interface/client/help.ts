/**
 * help.ts
 * 
 * CLI、ブラウザで共通して使用するヘルプ表示処理
 * ヘルプテキストの生成とフォーマット処理
 */

import { CommandInfo, HelpDisplayOptions } from './types.ts';

/**
 * グローバルヘルプを生成する
 * 
 * @param commands コマンド情報の配列
 * @param options 表示オプション
 * @returns フォーマット済みのヘルプテキスト
 */
export function generateGlobalHelp(
  commands: CommandInfo[], 
  options: HelpDisplayOptions = {}
): string {
  const format = options.format || 'text';
  const detailed = options.detailed || false;
  
  // 書式に応じたヘルプ生成処理を分岐
  switch (format) {
    case 'html':
      return generateHtmlGlobalHelp(commands, detailed);
    case 'markdown':
      return generateMarkdownGlobalHelp(commands, detailed);
    case 'text':
    default:
      return generateTextGlobalHelp(commands, detailed);
  }
}

/**
 * 特定コマンドのヘルプを生成する
 * 
 * @param command コマンド情報
 * @param options 表示オプション
 * @returns フォーマット済みのヘルプテキスト
 */
export function generateCommandHelp(
  command: CommandInfo, 
  options: HelpDisplayOptions = {}
): string {
  const format = options.format || 'text';
  const detailed = options.detailed || false;
  
  // 書式に応じたヘルプ生成処理を分岐
  switch (format) {
    case 'html':
      return generateHtmlCommandHelp(command, detailed);
    case 'markdown':
      return generateMarkdownCommandHelp(command, detailed);
    case 'text':
    default:
      return generateTextCommandHelp(command, detailed);
  }
}

/**
 * テキスト形式のグローバルヘルプを生成
 */
function generateTextGlobalHelp(commands: CommandInfo[], detailed: boolean): string {
  let help = "使用方法: cli.ts [コマンド] [オプション]\n\n";
  help += "利用可能なコマンド:\n";
  
  // コマンドを名前順にソート
  const sortedCommands = [...commands].sort((a, b) => 
    a.name.localeCompare(b.name)
  );
  
  for (const command of sortedCommands) {
    const aliases = command.aliases && command.aliases.length > 0
      ? ` (別名: ${command.aliases.join(", ")})`
      : "";
      
    help += `  ${command.name}${aliases}\n`;
    help += `    ${command.description}\n`;
    
    if (detailed && command.helpText) {
      help += `\n    ${command.helpText}\n`;
    }
    
    help += '\n';
  }
  
  help += "詳細なヘルプを表示するには: cli.ts help [コマンド名]\n";
  return help;
}

/**
 * HTML形式のグローバルヘルプを生成
 */
function generateHtmlGlobalHelp(commands: CommandInfo[], detailed: boolean): string {
  let html = `
    <div class="help-container">
      <h2>使用方法</h2>
      <code>cli.ts [コマンド] [オプション]</code>
      
      <h3>利用可能なコマンド</h3>
      <ul class="command-list">
  `;
  
  // コマンドを名前順にソート
  const sortedCommands = [...commands].sort((a, b) => 
    a.name.localeCompare(b.name)
  );
  
  for (const command of sortedCommands) {
    const aliases = command.aliases && command.aliases.length > 0
      ? ` <span class="aliases">(別名: ${command.aliases.join(", ")})</span>`
      : "";
      
    html += `
      <li class="command-item">
        <div class="command-name">${command.name}${aliases}</div>
        <div class="command-description">${command.description}</div>
    `;
    
    if (detailed && command.helpText) {
      html += `<div class="command-details">${command.helpText}</div>`;
    }
    
    html += `</li>`;
  }
  
  html += `
      </ul>
      <p class="help-footer">詳細なヘルプを表示するには: <code>cli.ts help [コマンド名]</code></p>
    </div>
  `;
  
  return html;
}

/**
 * Markdown形式のグローバルヘルプを生成
 */
function generateMarkdownGlobalHelp(commands: CommandInfo[], detailed: boolean): string {
  let md = "## 使用方法\n\n";
  md += "\`\`\`\ncli.ts [コマンド] [オプション]\n\`\`\`\n\n";
  md += "## 利用可能なコマンド\n\n";
  
  // コマンドを名前順にソート
  const sortedCommands = [...commands].sort((a, b) => 
    a.name.localeCompare(b.name)
  );
  
  for (const command of sortedCommands) {
    const aliases = command.aliases && command.aliases.length > 0
      ? ` (別名: ${command.aliases.join(", ")})`
      : "";
      
    md += `### ${command.name}${aliases}\n\n`;
    md += `${command.description}\n\n`;
    
    if (detailed && command.helpText) {
      md += `${command.helpText}\n\n`;
    }
  }
  
  md += "> 詳細なヘルプを表示するには: `cli.ts help [コマンド名]`\n";
  return md;
}

/**
 * テキスト形式の特定コマンドヘルプを生成
 */
function generateTextCommandHelp(command: CommandInfo, detailed: boolean): string {
  const aliases = command.aliases && command.aliases.length > 0
    ? ` (別名: ${command.aliases.join(", ")})`
    : "";
  
  let help = `コマンド: ${command.name}${aliases}\n\n`;
  help += `${command.description}\n\n`;
  
  if (detailed && command.helpText) {
    help += `詳細:\n${command.helpText}\n\n`;
  }
  
  help += "使用方法: cli.ts " + command.name + " [オプション]\n";
  return help;
}

/**
 * HTML形式の特定コマンドヘルプを生成
 */
function generateHtmlCommandHelp(command: CommandInfo, detailed: boolean): string {
  const aliases = command.aliases && command.aliases.length > 0
    ? ` <span class="aliases">(別名: ${command.aliases.join(", ")})</span>`
    : "";
  
  let html = `
    <div class="help-container">
      <h2>コマンド: ${command.name}${aliases}</h2>
      <div class="command-description">${command.description}</div>
  `;
  
  if (detailed && command.helpText) {
    html += `
      <h3>詳細</h3>
      <div class="command-details">${command.helpText}</div>
    `;
  }
  
  html += `
      <h3>使用方法</h3>
      <code>cli.ts ${command.name} [オプション]</code>
    </div>
  `;
  
  return html;
}

/**
 * Markdown形式の特定コマンドヘルプを生成
 */
function generateMarkdownCommandHelp(command: CommandInfo, detailed: boolean): string {
  const aliases = command.aliases && command.aliases.length > 0
    ? ` (別名: ${command.aliases.join(", ")})`
    : "";
  
  let md = `## コマンド: ${command.name}${aliases}\n\n`;
  md += `${command.description}\n\n`;
  
  if (detailed && command.helpText) {
    md += `### 詳細\n\n${command.helpText}\n\n`;
  }
  
  md += `### 使用方法\n\n\`\`\`\ncli.ts ${command.name} [オプション]\n\`\`\`\n`;
  return md;
}
