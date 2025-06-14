/**
 * commandPanel.ts
 * 
 * コマンド関連のUIコンポーネント
 */

import { CommandInfo } from '../../../client/types.ts';
import { generateGlobalHelp, generateCommandHelp } from '../../../client/help.ts';

/**
 * コマンドリストの更新
 */
export function updateCommandList(
  container: HTMLElement, 
  commands: CommandInfo[], 
  onSelectCommand: (name: string) => void
): void {
  if (!container) return;
  
  // コマンドリストを生成
  const htmlHelp = generateGlobalHelp(commands, { format: 'html', detailed: false });
  container.innerHTML = htmlHelp;
  
  // コマンド項目のクリックイベント設定
  const commandItems = container.querySelectorAll('.command-item');
  commandItems.forEach(item => {
    item.addEventListener('click', () => {
      const commandName = item.querySelector('.command-name')?.textContent?.split(' ')[0];
      if (commandName) {
        onSelectCommand(commandName);
      }
    });
  });
}

/**
 * コマンドのヘルプを表示
 */
export function showCommandHelp(
  container: HTMLElement, 
  command: CommandInfo, 
  onExecute: (command: string, args: string[]) => void
): void {
  if (!container) return;
  
  const htmlHelp = generateCommandHelp(command, { format: 'html', detailed: true });
  
  // ヘルプを表示
  container.innerHTML = `
    <h2>コマンド: ${command.name}</h2>
    ${htmlHelp}
    <div class="command-execute">
      <input type="text" id="command-args" placeholder="引数を入力">
      <button id="execute-btn">実行</button>
    </div>
    <div id="command-result"></div>
  `;
  
  // 実行ボタンのイベント設定
  const executeBtn = container.querySelector('#execute-btn');
  const argsInput = container.querySelector('#command-args') as HTMLInputElement;
  if (executeBtn && argsInput) {
    executeBtn.addEventListener('click', () => {
      const args = argsInput.value.split(' ').filter(arg => arg.trim() !== '');
      onExecute(command.name, args);
    });
  }
}

/**
 * コマンド実行結果の表示
 */
export function showCommandResult(container: HTMLElement, result: unknown | Error): void {
  if (!container) return;
  
  if (result instanceof Error) {
    container.innerHTML = `
      <div class="error">
        <h3>エラー:</h3>
        <p>${result.message}</p>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div class="success">
        <h3>実行結果:</h3>
        <pre>${JSON.stringify(result, null, 2)}</pre>
      </div>
    `;
  }
}
