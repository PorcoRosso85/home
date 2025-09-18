/**
 * commands.ts
 * 
 * コマンド管理の共通機能
 * CLI、ブラウザの両方で使用するコマンド処理を提供
 */

import { CommandInfo } from './types.ts';

/**
 * コマンドストア
 * コマンドの登録と取得を管理
 */
export class CommandStore {
  private commands: Map<string, CommandInfo> = new Map();
  
  /**
   * コマンドを登録
   * 
   * @param command 登録するコマンド情報
   */
  registerCommand(command: CommandInfo): void {
    // メインコマンド名で登録
    this.commands.set(command.name, command);
    
    // エイリアスがあれば登録
    if (command.aliases) {
      for (const alias of command.aliases) {
        this.commands.set(alias, command);
      }
    }
  }
  
  /**
   * 複数コマンドを一括登録
   * 
   * @param commands 登録するコマンド情報の配列
   */
  registerCommands(commands: CommandInfo[]): void {
    for (const command of commands) {
      this.registerCommand(command);
    }
  }
  
  /**
   * コマンドを名前で取得
   * 
   * @param name コマンド名またはエイリアス
   * @returns コマンド情報、見つからない場合はundefined
   */
  getCommand(name: string): CommandInfo | undefined {
    return this.commands.get(name);
  }
  
  /**
   * 登録されているすべてのコマンドを取得
   * エイリアスは除外し、一意のコマンドのみを返す
   * 
   * @returns コマンド情報の配列
   */
  getAllCommands(): CommandInfo[] {
    // 重複を排除するためにSetを使用
    const uniqueCommands = new Set<CommandInfo>();
    
    for (const command of this.commands.values()) {
      uniqueCommands.add(command);
    }
    
    return Array.from(uniqueCommands);
  }
  
  /**
   * コマンドの存在確認
   * 
   * @param name コマンド名またはエイリアス
   * @returns 存在する場合はtrue、そうでなければfalse
   */
  hasCommand(name: string): boolean {
    return this.commands.has(name);
  }
  
  /**
   * 登録されているコマンド数を取得
   * エイリアスも含む
   * 
   * @returns コマンド数
   */
  get size(): number {
    return this.commands.size;
  }
  
  /**
   * 一意のコマンド数を取得
   * エイリアスは除外
   * 
   * @returns 一意のコマンド数
   */
  get uniqueSize(): number {
    return this.getAllCommands().length;
  }
  
  /**
   * すべてのコマンドをクリア
   */
  clear(): void {
    this.commands.clear();
  }
}

/**
 * パス上のコマンドを読み込み、CommandStoreに登録する
 * 
 * @param commandsDir コマンドディレクトリのパス
 * @returns 登録されたコマンドの情報の配列
 */
export async function loadCommandsFromDirectory(
  commandsDir: string
): Promise<CommandInfo[]> {
  const commandStore = new CommandStore();
  
  try {
    // ディレクトリ内のすべての.tsファイルを検索
    for await (const entry of Deno.readDir(commandsDir)) {
      if (entry.isFile && entry.name.endsWith('.ts')) {
        try {
          // 動的インポート
          const importPath = `${commandsDir}/${entry.name}`;
          const fileUrl = `file://${importPath}`;
          const module = await import(fileUrl);
          
          // export { command } の形式をチェック
          if (module.command && module.command.name) {
            commandStore.registerCommand(module.command);
          }
        } catch (importError) {
          console.error(`コマンド '${entry.name}' のインポート中にエラーが発生しました:`, importError);
        }
      }
    }
  } catch (readError) {
    console.error(`ディレクトリ '${commandsDir}' の読み取り中にエラーが発生しました:`, readError);
  }
  
  return commandStore.getAllCommands();
}

/**
 * コマンドの実行結果型
 */
export interface CommandResult {
  /** 成功フラグ */
  success: boolean;
  /** データ */
  data?: unknown;
  /** エラーメッセージ */
  error?: string;
}

/**
 * コマンド実行インターフェース
 */
export interface CommandExecutor {
  /** コマンドを実行 */
  execute(commandName: string, args: string[]): Promise<CommandResult>;
}
