/**
 * commandLoader.ts
 * 
 * CLIコマンドを動的にロードするモジュール
 */

import { CliCommand } from '../cli.ts';
import { PathHandlingService } from '../../application/PathHandlingService.ts';

/**
 * CLIディレクトリからすべてのコマンドを動的に読み込む
 * @returns ロードされたコマンドの配列
 */
export async function loadCommands(): Promise<CliCommand[]> {
  const commands: CliCommand[] = [];
  
  try {
    // ファイルURLからパスを取得して、CLI コマンドディレクトリへのパスを解決
    const fileUrl = new URL(import.meta.url);
    const currentDir = fileUrl.pathname.substring(0, fileUrl.pathname.lastIndexOf('/'));
    const cliDir = `${currentDir}/../cli`;
    
    // PathHandlingServiceのインスタンスを作成
    const pathService = new PathHandlingService();
    
    // CLI ディレクトリのパスを正規化
    const normalizedCliDir = pathService.resolvePath(cliDir);
    
    console.log(`CLI コマンドディレクトリからコマンドをロードしています: ${normalizedCliDir}`);
    
    // ディレクトリ内のファイルをスキャン
    for await (const entry of Deno.readDir(normalizedCliDir)) {
      if (entry.isFile && entry.name.endsWith('.ts')) {
        try {
          // 動的インポート
          const importPath = `${normalizedCliDir}/${entry.name}`;
          const fileUrl = `file://${importPath}`;
          
          // モジュールをインポートしてコマンドを取得
          const module = await import(fileUrl);
          
          if (module.command && module.command.name) {
            commands.push(module.command);
            console.log(`コマンド '${module.command.name}' をロードしました`);
          } else {
            console.warn(`警告: '${entry.name}' には有効なコマンド定義がありません`);
          }
        } catch (importError) {
          console.error(`コマンド '${entry.name}' のインポート中にエラーが発生しました:`, importError);
        }
      }
    }
    
    // ロードされたコマンドの数をログ出力
    console.log(`合計 ${commands.length} 個のコマンドをロードしました`);
  } catch (error) {
    console.error('コマンドのロード中にエラーが発生しました:', error);
    throw error;
  }
  
  return commands;
}

