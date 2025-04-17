/**
 * JSONファイルからパス情報を抽出するユーティリティ
 * 主に要件定義ファイルからoutputPath情報を抽出し、依存関係を分析します
 */
import { join } from "https://deno.land/std@0.178.0/path/mod.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";

/**
 * 単一のJSONファイルから出力パス情報を抽出する
 * 
 * @param filePath JSONファイルのパス
 * @returns 抽出した情報オブジェクト
 */
export async function extractPathFromJson(filePath: string): Promise<any> {
  try {
    const content = await Deno.readTextFile(filePath);
    const json = JSON.parse(content);
    
    return {
      fileName: filePath.split('/').pop() || '',
      id: json.id || '',
      title: json.title || '',
      outputPath: json.outputPath?.default || '',
      implementationType: json.implementationType || ''
    };
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error);
    return {
      fileName: filePath.split('/').pop() || '',
      error: error.message
    };
  }
}

/**
 * ディレクトリ内のすべてのJSONファイルから出力パス情報を収集する
 * 
 * @param directoryPath JSONファイルが含まれるディレクトリ
 * @returns 抽出した情報オブジェクトの配列
 */
export async function loadPathsFromDirectory(directoryPath: string): Promise<any[]> {
  try {
    const files = [];
    
    for await (const entry of Deno.readDir(directoryPath)) {
      if (entry.isFile && entry.name.endsWith('.json')) {
        const filePath = join(directoryPath, entry.name);
        const fileInfo = await extractPathFromJson(filePath);
        files.push(fileInfo);
      }
    }
    
    return files;
  } catch (error) {
    console.error("Error loading files from directory:", error);
    return [];
  }
}

/**
 * 出力パスの情報からディレクトリツリーを構築する
 * 
 * @param files 出力パス情報を含むオブジェクトの配列
 * @returns ディレクトリツリー構造
 */
export function buildDirectoryTree(files: any[]): any {
  // ルートディレクトリを作成
  const root = {
    name: "/",
    type: "directory",
    children: {}
  };
  
  for (const file of files) {
    // 出力パスがない場合はスキップ
    if (!file.outputPath) continue;
    
    // パスの正規化（先頭と末尾のスラッシュを削除）
    let path = file.outputPath;
    if (path.startsWith('/')) {
      path = path.substring(1);
    }
    if (path.endsWith('/')) {
      path = path.slice(0, -1);
    }
    
    // パスを分解
    const parts = path.split('/');
    
    // ファイル名を取得（パスの最後の部分）
    const outputFileName = parts.pop();
    
    // 現在のノードをルートに設定
    let current = root;
    
    // パスの各部分に対してディレクトリを作成
    for (const part of parts) {
      if (!part) continue; // 空の部分はスキップ
      
      // このパス部分のディレクトリが存在しない場合は作成
      if (!current.children[part]) {
        current.children[part] = {
          name: part,
          type: "directory",
          children: {}
        };
      }
      
      // 現在のノードを更新
      current = current.children[part];
    }
    
    // ファイルをこのディレクトリに追加
    if (!current.files) {
      current.files = [];
    }
    
    current.files.push({
      name: outputFileName,
      sourceFile: file.fileName,
      id: file.id,
      title: file.title,
      type: "file",
      path: file.outputPath,
    });
  }
  
  return root;
}

/**
 * ディレクトリツリーから依存関係のパスを抽出する
 * 
 * @param tree ディレクトリツリー構造
 * @returns 出力パスの配列
 */
export function extractDependencyPaths(tree: any): string[] {
  const paths: string[] = [];
  
  function traverse(node: any, currentPath = '') {
    // ファイルを処理
    if (node.files && node.files.length > 0) {
      for (const file of node.files) {
        paths.push(file.path);
      }
    }
    
    // 子ディレクトリを再帰的に処理
    for (const [name, child] of Object.entries(node.children)) {
      const newPath = currentPath ? `${currentPath}/${name}` : name;
      traverse(child, newPath);
    }
  }
  
  traverse(tree);
  return paths;
}
