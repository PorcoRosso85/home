/**
 * KuzuDB DML Generator Tool
 * 
 * エンティティ定義からDMLクエリを生成するためのツール関数群
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync } from "fs";
import { join, parse, dirname } from "path";

// 定数
const QUERY_DIR = dirname(new URL(import.meta.url).pathname);
const DML_DIR = join(QUERY_DIR, "../../dml");
const TEMPLATE_DIR = join(DML_DIR, "templates");
const CYPHER_EXTENSION = ".cypher";
const JSON_EXTENSION = ".json";

// エンティティ定義の型
export type EntityProperty = {
  type: string;
  primary_key?: boolean;
  description?: string;
};

export type EntityDefinition = {
  entity_type: "node" | "edge";
  table_name: string;
  templates: string[];
  properties: Record<string, EntityProperty>;
  from_table?: string;
  to_table?: string;
};

/**
 * ディレクトリの存在を確認し、存在しない場合は作成する
 */
export function ensureDirectory(dirPath: string): void {
  if (!existsSync(dirPath)) {
    mkdirSync(dirPath, { recursive: true });
    console.log(`ディレクトリを作成しました: ${dirPath}`);
  }
}

/**
 * JSONエンティティファイルを読み込む
 */
export function loadJsonEntity(filePath: string): EntityDefinition {
  try {
    const content = readFileSync(filePath, { encoding: "utf-8" });
    return JSON.parse(content) as EntityDefinition;
  } catch (e) {
    throw new Error(`エンティティファイルの読み込みに失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}`);
  }
}

/**
 * テンプレートファイルを読み込む
 */
export function loadTemplate(templateName: string): string {
  const templatePath = join(TEMPLATE_DIR, `${templateName}${CYPHER_EXTENSION}`);
  
  if (!existsSync(templatePath)) {
    // デフォルトのテンプレートを返す
    if (templateName === "create_node") {
      return `// {table_name}ノードを作成するクエリ
CREATE ({var}:{table_name} {{{properties}}})
RETURN {var}`;
    } else if (templateName === "create_edge") {
      return `// {table_name}エッジを作成するクエリ
MATCH (from:{from_table} {{{from_match}}})
MATCH (to:{to_table} {{{to_match}}})
CREATE (from)-[{var}:{table_name} {{{properties}}}]->(to)
RETURN {var}`;
    } else if (templateName === "match_node") {
      return `// {table_name}ノードを検索するクエリ
MATCH ({var}:{table_name} {{{match_properties}}})
RETURN {var}`;
    } else if (templateName === "update_node") {
      return `// {table_name}ノードを更新するクエリ
MATCH ({var}:{table_name} {{{match_properties}}})
SET {var} = {{{set_properties}}}
RETURN {var}`;
    }
  }
  
  try {
    return readFileSync(templatePath, { encoding: "utf-8" });
  } catch (e) {
    console.warn(`警告: テンプレートの読み込みに失敗しました: ${templatePath}`);
    return "";
  }
}

/**
 * ノード作成クエリを生成する
 */
export function generateCreateNodeQuery(entity: EntityDefinition): string {
  const templateName = entity.entity_type === "node" ? "create_node" : "create_edge";
  const template = loadTemplate(templateName);
  const tableName = entity.table_name;
  const varName = tableName.toLowerCase();
  
  // プロパティ文字列を構築
  const properties: string[] = [];
  for (const [propName, propInfo] of Object.entries(entity.properties)) {
    properties.push(`${propName}: $${propName}`);
  }
  
  const propertiesStr = properties.join(", ");
  
  // テンプレート変数を置換
  let query = template
    .replace(/\{table_name\}/g, tableName)
    .replace(/\{var\}/g, varName)
    .replace(/\{properties\}/g, propertiesStr);
  
  // エッジの場合は追加の置換
  if (entity.entity_type === "edge" && entity.from_table && entity.to_table) {
    query = query
      .replace(/\{from_table\}/g, entity.from_table)
      .replace(/\{to_table\}/g, entity.to_table)
      .replace(/\{from_match\}/g, "id: $from_id") // プライマリキーが固定と仮定
      .replace(/\{to_match\}/g, "id: $to_id");    // プライマリキーが固定と仮定
  }
  
  return query;
}

/**
 * マッチクエリを生成する
 */
export function generateMatchQuery(entity: EntityDefinition): string {
  const templateName = entity.entity_type === "node" ? "match_node" : "match_edge";
  const template = loadTemplate(templateName);
  const tableName = entity.table_name;
  const varName = tableName.toLowerCase();
  
  // プライマリキーを見つける
  const primaryKeyProps: string[] = [];
  for (const [propName, propInfo] of Object.entries(entity.properties)) {
    if (propInfo.primary_key) {
      primaryKeyProps.push(`${propName}: $${propName}`);
    }
  }
  
  // プライマリキーがない場合は最初のプロパティを使用
  const matchPropertiesStr = primaryKeyProps.length > 0 
    ? primaryKeyProps.join(", ") 
    : Object.keys(entity.properties)[0] + `: $${Object.keys(entity.properties)[0]}`;
  
  // テンプレート変数を置換
  let query = template
    .replace(/\{table_name\}/g, tableName)
    .replace(/\{var\}/g, varName)
    .replace(/\{match_properties\}/g, matchPropertiesStr);
  
  return query;
}

/**
 * 更新クエリを生成する
 */
export function generateUpdateQuery(entity: EntityDefinition): string {
  const templateName = entity.entity_type === "node" ? "update_node" : "update_edge";
  const template = loadTemplate(templateName);
  const tableName = entity.table_name;
  const varName = tableName.toLowerCase();
  
  // プライマリキーを見つける
  const primaryKeyProps: string[] = [];
  const updateProps: string[] = [];
  
  for (const [propName, propInfo] of Object.entries(entity.properties)) {
    if (propInfo.primary_key) {
      primaryKeyProps.push(`${propName}: $${propName}`);
    } else {
      updateProps.push(`${propName}: $${propName}`);
    }
  }
  
  // プライマリキーがない場合は最初のプロパティを使用
  const matchPropertiesStr = primaryKeyProps.length > 0 
    ? primaryKeyProps.join(", ") 
    : Object.keys(entity.properties)[0] + `: $${Object.keys(entity.properties)[0]}`;
  
  const setPropertiesStr = updateProps.join(", ");
  
  // テンプレート変数を置換
  let query = template
    .replace(/\{table_name\}/g, tableName)
    .replace(/\{var\}/g, varName)
    .replace(/\{match_properties\}/g, matchPropertiesStr)
    .replace(/\{set_properties\}/g, setPropertiesStr);
  
  return query;
}

/**
 * エンティティとテンプレートタイプに基づいてクエリを生成する
 */
export function generateQuery(entity: EntityDefinition, templateType: string): string {
  if (templateType === "create") {
    return generateCreateNodeQuery(entity);
  } else if (templateType === "match") {
    return generateMatchQuery(entity);
  } else if (templateType === "update") {
    return generateUpdateQuery(entity);
  }
  
  return `// 未実装のテンプレート: ${templateType} for ${entity.entity_type}`;
}

/**
 * クエリをファイルに保存する
 */
export function saveQuery(query: string, filePath: string): void {
  try {
    writeFileSync(filePath, query, { encoding: "utf-8" });
    console.log(`クエリを保存しました: ${filePath}`);
  } catch (e) {
    console.error(`エラー: クエリの保存に失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}`);
  }
}

/**
 * エンティティ定義からDMLクエリを生成する
 */
export function processEntity(entityPath: string, outputDir: string = DML_DIR): void {
  try {
    // ディレクトリの存在を確認
    ensureDirectory(outputDir);
    
    // エンティティを読み込む
    const entity = loadJsonEntity(entityPath);
    const tableName = entity.table_name;
    
    // 生成するテンプレートの種類
    const templates = entity.templates || ["create"];
    
    for (const templateType of templates) {
      const query = generateQuery(entity, templateType);
      const fileName = `${templateType}_${tableName.toLowerCase()}${CYPHER_EXTENSION}`;
      const outputPath = join(outputDir, fileName);
      saveQuery(query, outputPath);
    }
    
    console.log(`エンティティ ${tableName} のDMLクエリを生成しました`);
  } catch (e) {
    console.error(`エラー: エンティティの処理に失敗しました: ${entityPath} - ${e instanceof Error ? e.message : String(e)}`);
  }
}

/**
 * すべてのJSONエンティティ定義からDMLクエリを生成する
 */
export function processAllEntities(inputDir: string = DML_DIR, outputDir: string = DML_DIR): void {
  try {
    // ディレクトリの存在を確認
    ensureDirectory(outputDir);
    
    // JSONエンティティファイルを検索
    const entityFiles = readdirSync(inputDir)
      .filter(file => file.endsWith(JSON_EXTENSION));
    
    if (entityFiles.length === 0) {
      console.warn(`警告: ${inputDir} ディレクトリにJSONエンティティファイルがありません`);
      return;
    }
    
    // 各エンティティを処理
    for (const entityFile of entityFiles) {
      const entityPath = join(inputDir, entityFile);
      processEntity(entityPath, outputDir);
    }
    
    console.log(`すべてのエンティティのDMLクエリを生成しました（合計: ${entityFiles.length}）`);
  } catch (e) {
    console.error(`エラー: エンティティの処理に失敗しました - ${e instanceof Error ? e.message : String(e)}`);
  }
}

// コマンドライン呼び出し用
if (typeof require !== 'undefined' && require.main === module) {
  // コマンドライン引数の処理
  const args = process.argv.slice(2);
  
  if (args.includes('--all')) {
    processAllEntities();
  } else if (args.includes('--entity')) {
    const entityIndex = args.indexOf('--entity');
    if (entityIndex >= 0 && entityIndex + 1 < args.length) {
      processEntity(args[entityIndex + 1]);
    } else {
      console.error('エラー: --entity オプションの後にファイルパスを指定してください');
      process.exit(1);
    }
  } else {
    console.log('使用方法:');
    console.log('  --all              すべてのエンティティ定義からDMLを生成');
    console.log('  --entity FILE      指定したエンティティ定義からDMLを生成');
    process.exit(1);
  }
}
