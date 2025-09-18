// core/output/outputFormatters.ts - 出力フォーマッタ

import { DependencyMap, FileSystem } from '../types.ts';
import { printToConsole } from './outputHandler.ts';

/**
 * 依存関係グラフを基本形式で出力する関数
 * 
 * 出力例:
 * ```json
 * {
 *   "要件定義.json": [
 *     "機能要件.json",
 *     "非機能要件.json"
 *   ],
 *   "機能要件.json": [
 *     "ユーザー管理機能.json"
 *   ],
 *   "ユーザー管理機能.json": [],
 *   "非機能要件.json": []
 * }
 * ```
 */
export function outputBasicFormat(dependencies: DependencyMap, formattedResult: string): void {
  printToConsole(formattedResult);
}

/**
 * 新しい出力形式のための関数テンプレート
 * (ここに新しい出力形式を実装することができます)
 * 
 * 出力例:
 * ```
 * 要件定義.json
 * ├── 機能要件.json
 * │   └── ユーザー管理機能.json
 * └── 非機能要件.json
 * ```
 */
export function outputTreeFormat(dependencies: DependencyMap): void {
  // ツリー表示の実装
  // TODO: 実装する
}

/**
 * マークダウン形式で出力する関数
 * 各ファイルのtitleとdescriptionを含んだ階層構造のマークダウンを生成する
 * 
 * 出力例:
 * ```markdown
 * # 要件定義
 * システム要件定義のルート
 * 
 * ## 機能要件
 * システムの機能要件に関する定義
 * 
 * ### ユーザー管理機能
 * システムのユーザー管理機能に関する要件定義
 * 
 * ## 非機能要件
 * システムの非機能要件に関する定義
 * ```
 */
export async function outputMarkdownFormat(dependencies: DependencyMap, fs: FileSystem, baseDir: string): Promise<void> {
  // ルートノードを見つける（依存されるが他に依存しないノード）
  const rootNodes = findRootNodes(dependencies);
  if (rootNodes.length === 0) {
    printToConsole("マークダウン出力エラー: ルートノードが見つかりません。");
    return;
  }

  // 通常は1つのルートノードを処理
  const rootNode = rootNodes[0];
  const markdownContent = await buildMarkdownTree(rootNode, dependencies, fs, baseDir, 1);
  
  // 結果を表示
  printToConsole(markdownContent);
}

/**
 * 依存関係グラフからルートノードを見つける
 * （他のノードから依存されるが、自身は他に依存していないノード）
 */
function findRootNodes(dependencies: DependencyMap): string[] {
  // 全ノードのセット
  const allNodes = new Set<string>(Object.keys(dependencies));
  
  // 依存されるノードのセット
  const dependedNodes = new Set<string>();
  for (const deps of Object.values(dependencies)) {
    for (const dep of deps) {
      dependedNodes.add(dep);
    }
  }
  
  // 依存しているノードのセット
  const dependingNodes = new Set<string>();
  for (const [node, deps] of Object.entries(dependencies)) {
    if (deps.length > 0) {
      dependingNodes.add(node);
    }
  }
  
  // 依存されるが自身は依存していないノード = リーフノード
  const leafNodes: string[] = [];
  for (const node of dependedNodes) {
    if (!dependingNodes.has(node)) {
      leafNodes.push(node);
    }
  }
  
  // 他のノードを依存するが、依存されない始点ノード = ルートノード
  const rootNodes: string[] = [];
  for (const node of dependingNodes) {
    if (!dependedNodes.has(node)) {
      rootNodes.push(node);
    }
  }
  
  // ルートノードが見つからない場合は、すべてのノードから依存されているノードを選択
  if (rootNodes.length === 0) {
    // 最も多く依存されているノード
    let maxDependedCount = 0;
    let maxDependedNode = '';
    
    const dependencyCount = new Map<string, number>();
    for (const deps of Object.values(dependencies)) {
      for (const dep of deps) {
        const count = (dependencyCount.get(dep) || 0) + 1;
        dependencyCount.set(dep, count);
        
        if (count > maxDependedCount) {
          maxDependedCount = count;
          maxDependedNode = dep;
        }
      }
    }
    
    if (maxDependedNode) {
      rootNodes.push(maxDependedNode);
    } else if (allNodes.size > 0) {
      // 依存関係がない場合は最初のノードを選択
      rootNodes.push(Array.from(allNodes)[0]);
    }
  }
  
  return rootNodes;
}

/**
 * JSONファイルからデータを抽出する
 */
async function extractJsonData(filePath: string, fs: FileSystem, baseDir: string): Promise<{ title: string; description: string }> {
  try {
    // 絶対パスを構築（ファイル名が相対パスの場合）
    const absolutePath = filePath.startsWith('/') 
      ? filePath 
      : baseDir + '/' + filePath;
    
    const fileContent = await fs.readTextFile(absolutePath);
    const jsonData = JSON.parse(fileContent);
    
    return {
      title: jsonData.title || pathToName(filePath),
      description: jsonData.description || ""
    };
  } catch (error) {
    return {
      title: pathToName(filePath),
      description: "データを読み込めませんでした"
    };
  }
}

/**
 * ファイルパスからファイル名を抽出する
 */
function pathToName(filePath: string): string {
  const parts = filePath.split("/");
  return parts[parts.length - 1];
}

/**
 * マークダウンツリーを再帰的に構築する
 */
async function buildMarkdownTree(
  node: string, 
  dependencies: DependencyMap, 
  fs: FileSystem, 
  baseDir: string,
  level: number, 
  visited = new Set<string>()
): Promise<string> {
  // 循環参照を防止
  if (visited.has(node)) {
    return `${"#".repeat(level)} ${pathToName(node)} (循環参照)\n\n`;
  }
  visited.add(node);
  
  const { title, description } = await extractJsonData(node, fs, baseDir);
  let markdown = `${"#".repeat(level)} ${title}\n${description}\n\n`;
  
  // 依存しているノードを再帰的に処理
  const deps = dependencies[node] || [];
  for (const dep of deps) {
    markdown += await buildMarkdownTree(dep, dependencies, fs, baseDir, level + 1, new Set(visited));
  }
  
  return markdown;
}
/**
 * HTMLフォーマットで出力する関数テンプレート
 * 
 * 出力例:
 * ```html
 * <ul>
 *   <li>要件定義.json
 *     <ul>
 *       <li>機能要件.json
 *         <ul>
 *           <li>ユーザー管理機能.json</li>
 *         </ul>
 *       </li>
 *       <li>非機能要件.json</li>
 *     </ul>
 *   </li>
 * </ul>
 * ```
 */
export function outputHtmlFormat(dependencies: DependencyMap): void {
  // HTML出力の実装
  // TODO: 実装する
}
