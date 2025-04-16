/**
 * referenceAnalyzer.ts
 * 
 * スキーマ参照関連の分析機能を提供する純粋関数群
 * クリーンアーキテクチャのドメイン層に位置する
 */

/**
 * スキーマ参照情報
 * JSONスキーマの$refによって参照される型の情報を表現する
 */
export type SchemaReference = {
  /** 参照される型のID */
  typeId: string;
  /** 参照元のメタスキーマソース */
  metaSource: string;
  /** 参照元のメタスキーマID */
  metaId: string;
};

/**
 * 型の依存関係
 * 型の依存関係のツリー構造を表現する
 */
export type TypeDependency = {
  /** 型の名前 */
  name: string;
  /** メタスキーマ名 */
  metaSchema: string;
  /** スキーマ内での参照パス */
  path: string;
  /** 依存する型のリスト */
  dependencies: TypeDependency[];
};

/**
 * URIからスキーマ参照情報を解析する純粋関数
 * 
 * @param uri $refで指定されたURI文字列
 * @returns 解析されたスキーマ参照情報、解析できない場合はnull
 */
export function parseReference(uri: string): SchemaReference | null {
  // 標準的な参照形式: "meta://[source]/[metaId]#/definitions/[typeId]"
  const metaRegex = /^meta:\/\/([^/]+)\/([^#]+)#\/definitions\/(.+)$/;
  const metaMatch = uri.match(metaRegex);
  
  if (metaMatch) {
    const [, metaSource, metaId, typeId] = metaMatch;
    return { metaSource, metaId, typeId };
  }
  
  // ファイル参照形式: "UserRegister__Function.json"
  // この形式は外部依存関係で使用される
  const fileRegex = /^(.+)__Function\.json$/;
  const fileMatch = uri.match(fileRegex);
  
  if (fileMatch) {
    const [, typeId] = fileMatch;
    return { 
      metaSource: "function", 
      metaId: "schema", 
      typeId 
    };
  }
  
  return null;
}

/**
 * 依存関係を文字列表現に変換（ツリー形式）
 * 
 * @param dependency 依存関係ツリー
 * @param indent インデントレベル（再帰呼び出し用）
 * @returns 整形された依存関係ツリーの文字列表現
 */
export function dependencyToString(dependency: TypeDependency, indent: number = 0): string {
  const indentStr = '  '.repeat(indent);
  let result = `${indentStr}${dependency.name} (${dependency.metaSchema})`;
  
  if (dependency.path) {
    result += ` [${dependency.path}]`;
  }
  
  if (dependency.dependencies.length > 0) {
    result += ' {\n';
    for (const dep of dependency.dependencies) {
      result += dependencyToString(dep, indent + 1) + '\n';
    }
    result += `${indentStr}}`;
  }
  
  return result;
}

/**
 * 依存関係ツリーをフラットな配列に変換
 * 
 * @param dependency 依存関係ツリー
 * @returns フラットな依存関係の配列
 */
export function flattenDependencies(dependency: TypeDependency): TypeDependency[] {
  const result: TypeDependency[] = [dependency];
  
  for (const dep of dependency.dependencies) {
    result.push(...flattenDependencies(dep));
  }
  
  return result;
}

/**
 * 依存関係ツリーからユニークな依存型のリストを抽出
 * 
 * @param dependency 依存関係ツリー
 * @returns ユニークな依存型名の配列
 */
export function getUniqueDependencyTypes(dependency: TypeDependency): string[] {
  const flatDeps = flattenDependencies(dependency);
  const uniqueTypes = new Set<string>();
  
  for (const dep of flatDeps) {
    uniqueTypes.add(dep.name);
  }
  
  return Array.from(uniqueTypes).sort();
}
