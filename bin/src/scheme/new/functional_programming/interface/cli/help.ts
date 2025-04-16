#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --check
/**
 * help.ts
 * 
 * ヘルプコマンドの実装
 * すべてのコマンドのヘルプ情報を提供します
 */

import { CliCommand } from '../cli.ts';

/**
 * ヘルプコマンドの実装
 */
export const command: CliCommand = {
  name: "help",
  aliases: ["h", "--help", "-h"],
  description: "コマンドのヘルプ情報を表示します",
  
  /**
   * ヘルプコマンドを実行する
   * @param args 引数配列
   */
  async execute(args: string[]): Promise<void> {
    if (args.length > 0) {
      // 特定コマンドのヘルプを表示
      const commandName = args[0];
      const fileUrl = new URL(import.meta.url);
      const cliDir = fileUrl.pathname.substring(0, fileUrl.pathname.lastIndexOf('/'));
      
      try {
        // コマンドをロード
        for await (const entry of Deno.readDir(cliDir)) {
          if (entry.isFile && entry.name.endsWith('.ts')) {
            try {
              const moduleUrl = `file://${cliDir}/${entry.name}`;
              const module = await import(moduleUrl);
              
              if (module.command && 
                  (module.command.name === commandName || 
                   (module.command.aliases && module.command.aliases.includes(commandName)))) {
                // 見つかったコマンドのヘルプを表示
                module.command.showHelp();
                return;
              }
            } catch (importError) {
              console.error(`コマンドのインポート中にエラーが発生しました:`, importError);
            }
          }
        }
        
        // コマンドが見つからない場合
        console.error(`エラー: コマンド '${commandName}' が見つかりませんでした`);
      } catch (error) {
        console.error(`ヘルプ表示中にエラーが発生しました:`, error);
      }
    } else {
      // 全コマンドの概要を表示
      this.showHelp();
    }
  },
  
  /**
   * ヘルプ情報を表示する
   */
  showHelp(): void {
    console.log("使用方法: cli.ts help [コマンド名]");
    console.log("");
    console.log("説明:");
    console.log("  コマンドのヘルプ情報を表示します。コマンド名を指定すると");
    console.log("  そのコマンドの詳細なヘルプが表示されます。");
    console.log("");
    console.log("引数:");
    console.log("  [コマンド名]  オプション: ヘルプを表示するコマンド名");
    console.log("");
    console.log("例:");
    console.log("  cli.ts help             # すべてのコマンドの概要を表示");
    console.log("  cli.ts help generate    # generateコマンドの詳細を表示");
    console.log("  cli.ts help deps        # depsコマンドの詳細を表示");
  }
};
