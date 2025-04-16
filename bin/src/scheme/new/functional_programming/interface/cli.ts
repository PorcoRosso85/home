#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --allow-env --no-check
/**
 * cli.ts
 * 
 * 関数型スキーマ生成CLIのメインエントリポイント
 * コマンドの動的ロードと実行を担当する
 */

import * as path from 'node:path';

/**
 * コマンドインターフェース
 */
export interface CliCommand {
  name: string;
  aliases?: string[];
  description: string;
  execute(args: string[]): Promise<void>;
  showHelp(): void;
}

// コマンドレジストリ
const commands: Map<string, CliCommand> = new Map();

/**
 * コマンドディレクトリからすべてのコマンドを動的にロードする
 */
async function loadCommands(): Promise<void> {
  try {
    // ./cli/ ディレクトリ内のすべての.tsファイルを検索
    const fileUrl = new URL(import.meta.url);
    const currentDir = fileUrl.pathname.substring(0, fileUrl.pathname.lastIndexOf('/'));
    const cliDir = `${currentDir}/cli`;
    
    try {
      console.log(`コマンドディレクトリを読み取り中: ${cliDir}`);
      for await (const entry of Deno.readDir(cliDir)) {
        console.log(`ファイル発見: ${entry.name} (種類: ${entry.isFile ? 'ファイル' : 'ディレクトリ'})`);
        if (entry.isFile && entry.name.endsWith('.ts')) {
          try {
            // 動的インポート
            const importPath = `${cliDir}/${entry.name}`;
            const fileUrl = `file://${importPath}`;
            console.log(`ファイルを読み込み中: ${fileUrl}`);
            const module = await import(fileUrl);
            console.log(`ファイル読み込み成功: ${entry.name}, モジュールの中身:`, Object.keys(module));
            
            if (module.command && module.command.name) {
              // メインコマンド登録
              commands.set(module.command.name, module.command);
              
              // エイリアス登録
              if (module.command.aliases) {
                for (const alias of module.command.aliases) {
                  commands.set(alias, module.command);
                }
              }
              
              console.log(`コマンド '${module.command.name}' を登録しました (ファイル: ${entry.name})`);
            }
          } catch (importError) {
            console.error(`コマンド '${entry.name}' のインポート中にエラーが発生しました:`, importError);
            if (importError instanceof Error) {
              console.error(`エラー詳細: ${importError.message}`);
              console.error(`スタックトレース: ${importError.stack}`);
            }
          }
        }
      }
    } catch (readError) {
      console.error(`ディレクトリ '${cliDir}' の読み取り中にエラーが発生しました:`, readError);
    }

    // コマンドが見つからない場合は警告
    if (commands.size === 0) {
      console.warn(`警告: コマンドが見つかりませんでした。'${cliDir}' ディレクトリを確認してください。`);
    }
  } catch (error) {
    console.error(`コマンドロード中にエラーが発生しました:`, error);
  }
}

/**
 * すべてのコマンドのヘルプを表示する
 */
function showGlobalHelp(): void {
  console.log("使用方法: cli.ts [コマンド] [オプション]");
  console.log("");
  console.log("利用可能なコマンド:");
  
  // コマンドを名前順にソート
  const sortedCommands = Array.from(new Set(commands.values()))
    .sort((a, b) => a.name.localeCompare(b.name));
  
  for (const command of sortedCommands) {
    const aliases = command.aliases && command.aliases.length > 0
      ? ` (別名: ${command.aliases.join(", ")})`
      : "";
      
    console.log(`  ${command.name}${aliases}`);
    console.log(`    ${command.description}`);
    console.log();
  }
  
  console.log("詳細なヘルプを表示するには: cli.ts help [コマンド名]");
}

/**
 * CLIエントリポイント
 */
export async function main(args: string[]): Promise<void> {
  await loadCommands();
  
  // コマンド名を取得
  const commandName = args[0] || "help";
  
  // ヘルプコマンドの特別処理
  if (commandName === "help") {
    const helpTarget = args[1];
    if (helpTarget && commands.has(helpTarget)) {
      // 特定コマンドのヘルプを表示
      commands.get(helpTarget)!.showHelp();
    } else {
      // グローバルヘルプを表示
      showGlobalHelp();
    }
    return;
  }
  
  // コマンドを実行
  const command = commands.get(commandName);
  if (command) {
    await command.execute(args.slice(1));
  } else {
    console.error(`エラー: コマンド '${commandName}' が見つかりませんでした`);
    showGlobalHelp();
  }
}

// メインエントリポイント
if (import.meta.main) {
  main(Deno.args)
    .catch(error => {
      console.error(`実行エラー:`, error);
      Deno.exit(1);
    });
}
