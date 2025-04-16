// core/formatter/dependencyFormatter.ts - 依存関係グラフのフォーマット機能

import { DependencyMap, PathUtils } from '../types.ts';

/**
 * 相対パスに変換する関数
 */
export function toRelativePath(
  path: string,
  baseDir: string,
  pathUtils: PathUtils
): string {
  return path.startsWith(baseDir) 
    ? pathUtils.relative(baseDir, path)
    : path;
}

/**
 * 依存関係グラフを相対パスに変換する
 */
export function formatWithRelativePaths(
  dependencies: DependencyMap,
  baseDir: string,
  pathUtils: PathUtils
): DependencyMap {
  const result: DependencyMap = {};
  
  for (const [file, deps] of Object.entries(dependencies)) {
    const relativeFile = toRelativePath(file, baseDir, pathUtils);
    result[relativeFile] = deps.map(dep => toRelativePath(dep, baseDir, pathUtils));
  }
  
  return result;
}

/**
 * 依存関係グラフをJSON文字列に変換する
 */
export function formatAsJson(
  dependencies: DependencyMap,
  pretty = true,
  space = 2
): string {
  return pretty
    ? JSON.stringify(dependencies, null, space)
    : JSON.stringify(dependencies);
}

/**
 * 依存関係グラフをテキスト形式に変換する
 */
export function formatAsText(dependencies: DependencyMap): string {
  const lines: string[] = ['依存関係グラフ:'];
  
  for (const [file, deps] of Object.entries(dependencies)) {
    lines.push(`${file}:`);
    
    if (deps.length === 0) {
      lines.push('  依存なし');
    } else {
      deps.forEach(dep => {
        lines.push(`  → ${dep}`);
      });
    }
    
    lines.push('');
  }
  
  return lines.join('\n');
}

/**
 * 依存関係グラフをDOT形式（Graphviz用）に変換する
 */
export function formatAsDot(dependencies: DependencyMap): string {
  const lines = ['digraph DependencyGraph {'];
  lines.push('  node [shape=box];');
  lines.push('');
  
  // ノードの定義
  for (const file of Object.keys(dependencies)) {
    // ファイル名をIDとして使用できるように正規化
    const nodeId = file.replace(/[^a-zA-Z0-9]/g, '_');
    lines.push(`  ${nodeId} [label="${file}"];`);
  }
  
  lines.push('');
  
  // エッジの定義
  for (const [file, deps] of Object.entries(dependencies)) {
    const sourceId = file.replace(/[^a-zA-Z0-9]/g, '_');
    
    for (const dep of deps) {
      const targetId = dep.replace(/[^a-zA-Z0-9]/g, '_');
      lines.push(`  ${sourceId} -> ${targetId};`);
    }
  }
  
  lines.push('}');
  return lines.join('\n');
}
