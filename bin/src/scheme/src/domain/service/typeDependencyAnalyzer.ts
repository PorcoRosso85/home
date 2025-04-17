import { FileSystemReader } from "../../infrastructure/fileSystemReader.ts";
import { SchemaReferenceResolver } from "./schemaReferenceResolver.ts";

/**
 * 型の依存関係を表すインターフェース
 */
export interface TypeDependency {
  name: string;
  metaSchema: string;
  path: string;
  dependencies: TypeDependency[];
}

/**
 * 型の依存関係を再帰的に取得する
 * 
 * @param typeName 型の名前
 * @param metaSchema メタスキーマの名前
 * @param fileReader ファイル読み込みオブジェクト
 * @param schemaDir スキーマファイルが格納されているディレクトリパス
 * @param visitedTypes 循環参照検出用の訪問済み型セット（内部再帰用）
 * @returns 型の依存関係ツリー
 */
export async function getDependencies(
  typeName: string,
  metaSchema: string,
  fileReader: FileSystemReader,
  schemaDir: string = "./data/generated",
  visitedTypes: Set<string> = new Set<string>()
): Promise<TypeDependency> {
  // 型の完全な識別子を作成（例: "User.Struct"）
  const typeId = `${typeName}.${metaSchema}`;
  
  // 循環参照の検出
  if (visitedTypes.has(typeId)) {
    // 循環参照の場合は依存関係なしの基本情報のみ返す
    return {
      name: typeName,
      metaSchema: metaSchema,
      path: `${schemaDir}/${typeName}.${metaSchema}.schema.json`,
      dependencies: [], // 循環参照検出時は空の依存関係を返す
    };
  }
  
  // 訪問済み型に追加
  visitedTypes.add(typeId);
  
  // スキーマファイルのパス
  const schemaPath = `${schemaDir}/${typeName}.${metaSchema}.schema.json`;
  
  try {
    // スキーマファイルを読み込む
    const schema = await fileReader.readJsonFile(schemaPath);
    
    // 依存関係を格納する配列
    const dependencies: TypeDependency[] = [];
    
    // スキーマから$ref属性を検索して依存関係を抽出
    await findReferences(schema, dependencies, fileReader, schemaDir, new Set(visitedTypes));
    
    // 結果を返す
    return {
      name: typeName,
      metaSchema: metaSchema,
      path: schemaPath,
      dependencies: dependencies,
    };
  } catch (error) {
    console.error(`型 ${typeId} の依存関係取得中にエラーが発生しました: ${error.message}`);
    
    // エラーが発生した場合は空の依存関係を返す
    return {
      name: typeName,
      metaSchema: metaSchema,
      path: schemaPath,
      dependencies: [],
    };
  }
}

/**
 * オブジェクト内の$ref属性を再帰的に検索し、依存関係を抽出する
 * 
 * @param obj 検査対象のオブジェクト
 * @param dependencies 依存関係を格納する配列
 * @param fileReader ファイル読み込みオブジェクト
 * @param schemaDir スキーマファイルが格納されているディレクトリパス
 * @param visitedTypes 循環参照検出用の訪問済み型セット
 */
async function findReferences(
  obj: any,
  dependencies: TypeDependency[],
  fileReader: FileSystemReader,
  schemaDir: string,
  visitedTypes: Set<string>
): Promise<void> {
  // nullまたは未定義の場合は処理しない
  if (obj === null || obj === undefined) {
    return;
  }
  
  // オブジェクト型でない場合は処理しない
  if (typeof obj !== 'object') {
    return;
  }
  
  // 配列の場合は各要素を再帰的に処理
  if (Array.isArray(obj)) {
    for (const item of obj) {
      await findReferences(item, dependencies, fileReader, schemaDir, visitedTypes);
    }
    return;
  }
  
  const refResolver = new SchemaReferenceResolver(fileReader, schemaDir);
  
  // オブジェクト内の各プロパティを処理
  for (const [key, value] of Object.entries(obj)) {
    // $ref属性を検出した場合
    if (key === '$ref' && typeof value === 'string') {
      // 新しいURI形式の参照かチェック
      if (value.startsWith('scheme://')) {
        // URIから参照情報を解析
        const reference = refResolver.parseReference(value);
        if (reference) {
          const refTypeName = reference.typeId;
          const refMetaSchema = reference.metaId;
          const refTypeId = `${refTypeName}.${refMetaSchema}`;
          
          // 既に処理済みの依存関係でなければ追加
          if (!dependencies.some(dep => `${dep.name}.${dep.metaSchema}` === refTypeId)) {
            // 依存先の型の依存関係を再帰的に取得
            const dependency = await getDependencies(
              refTypeName,
              refMetaSchema,
              fileReader,
              schemaDir,
              visitedTypes
            );
            
            // 依存関係リストに追加
            dependencies.push(dependency);
          }
        }
      }
      // 旧形式のファイルパス参照の場合
      else if (value.endsWith('.schema.json')) {
        // ファイル名から型名とメタスキーマを抽出
        const match = value.match(/([^\/]+)\.([^\/]+)\.schema\.json$/);
        if (match) {
          const refTypeName = match[1];
          const refMetaSchema = match[2];
          const refTypeId = `${refTypeName}.${refMetaSchema}`;
          
          // 既に処理済みの依存関係でなければ追加
          if (!dependencies.some(dep => `${dep.name}.${dep.metaSchema}` === refTypeId)) {
            // 依存先の型の依存関係を再帰的に取得
            const dependency = await getDependencies(
              refTypeName,
              refMetaSchema,
              fileReader,
              schemaDir,
              visitedTypes
            );
            
            // 依存関係リストに追加
            dependencies.push(dependency);
          }
        }
      }
    }
    // オブジェクト型の値は再帰的に検査
    else if (typeof value === 'object' && value !== null) {
      await findReferences(value, dependencies, fileReader, schemaDir, visitedTypes);
    }
  }
}

/**
 * 型の依存関係を文字列表現に変換（ツリー形式）
 * 
 * @param dependency 型の依存関係
 * @param indent インデントレベル（再帰呼び出し用）
 * @returns 文字列表現
 */
export function dependencyToString(dependency: TypeDependency, indent: number = 0): string {
  // インデント文字列を作成
  const indentStr = '  '.repeat(indent);
  
  // 基本情報を文字列化
  let result = `${indentStr}${dependency.name} (${dependency.metaSchema})\n`;
  
  // 依存関係を再帰的に文字列化
  for (const dep of dependency.dependencies) {
    result += dependencyToString(dep, indent + 1);
  }
  
  return result;
}
