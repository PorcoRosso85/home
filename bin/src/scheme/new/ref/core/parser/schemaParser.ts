// core/parser/schemaParser.ts - スキーマ解析のコア機能

import { SchemaCache, DependencyMap, FileSystem, PathUtils } from '../types.ts';

// 既定の設定
export const DEFAULT_SCHEMA_EXTENSIONS = ['.json'];
export const DEFAULT_EXCLUDE_PATTERNS = ['node_modules', '.git', 'dist', 'build'];
export const DEFAULT_REF_KEYWORDS = ['$ref'];

/**
 * ディレクトリ内のJSONスキーマファイルを再帰的に探索する
 */
export async function findSchemaFiles(
  dir: string,
  fs: FileSystem,
  pathUtils: PathUtils,
  extensions = DEFAULT_SCHEMA_EXTENSIONS,
  excludePatterns = DEFAULT_EXCLUDE_PATTERNS,
  debug = false
): Promise<string[]> {
  const schemaFiles: string[] = [];
  
  // ディレクトリを再帰的に探索する関数
  async function scanDir(currentDir: string) {
    try {
      const entries = await fs.listDir(currentDir);
      
      for (const entry of entries) {
        // 除外パターンに一致するかチェック
        if (excludePatterns.some(pattern => entry.name.includes(pattern))) {
          continue;
        }
        
        if (entry.isDirectory) {
          // ディレクトリの場合は再帰的に探索
          await scanDir(entry.path);
        } else if (entry.isFile) {
          // ファイルの場合は拡張子をチェック
          const fileExt = pathUtils.extname(entry.name).toLowerCase();
          if (extensions.includes(fileExt)) {
            // JSONファイルの内容をチェック
            try {
              const content = await fs.readTextFile(entry.path);
              const json = JSON.parse(content);
              // スキーマファイルのみを対象とする ($schemaキーを持つもの)
              if (json.$schema && typeof json.$schema === 'string') {
                schemaFiles.push(entry.path);
              }
            } catch (error: any) {
              // 読み込みエラーやJSON解析エラーは無視
              if (debug) {
                console.error(`${entry.path}の読み込みでエラー: ${error.message}`);
              }
            }
          }
        }
      }
    } catch (error: any) {
      console.error(`ディレクトリ ${currentDir} の読み取りに失敗: ${error.message}`);
    }
  }
  
  await scanDir(dir);
  return schemaFiles;
}

/**
 * JSONスキーマの依存関係を抽出する
 */
export async function extractDependencies(
  schemaPath: string,
  fs: FileSystem,
  pathUtils: PathUtils,
  baseDir: string,
  refKeywords = DEFAULT_REF_KEYWORDS
): Promise<DependencyMap> {
  const dependencies: DependencyMap = {};
  const visited = new Set<string>();
  
  // スキーマの絶対パスを取得
  const absolutePath = schemaPath.startsWith('/')
    ? schemaPath
    : pathUtils.join(baseDir, schemaPath);
  
  await findDependencies(absolutePath, dependencies, visited, fs, pathUtils, baseDir, refKeywords);
  
  return dependencies;
}

/**
 * すべてのスキーマの依存関係を抽出する
 */
export async function extractAllDependencies(
  baseDir: string,
  fs: FileSystem,
  pathUtils: PathUtils,
  extensions = DEFAULT_SCHEMA_EXTENSIONS,
  excludePatterns = DEFAULT_EXCLUDE_PATTERNS,
  refKeywords = DEFAULT_REF_KEYWORDS,
  debug = false
): Promise<DependencyMap> {
  const dependencies: DependencyMap = {};
  const visited = new Set<string>();
  
  // すべてのスキーマファイルを見つける
  const schemaFiles = await findSchemaFiles(baseDir, fs, pathUtils, extensions, excludePatterns, debug);
  
  // 各スキーマの依存関係を抽出
  for (const schemaFile of schemaFiles) {
    if (debug) {
      console.log(`スキーマファイル ${schemaFile} を処理中...`);
    }
    await findDependencies(schemaFile, dependencies, visited, fs, pathUtils, baseDir, refKeywords);
  }
  
  return dependencies;
}

/**
 * JSONスキーマの参照を解決する
 */
export async function bundleSchema(
  schemaPath: string,
  fs: FileSystem,
  pathUtils: PathUtils,
  baseDir: string
): Promise<any> {
  // スキーマキャッシュを初期化
  const schemaCache: SchemaCache = {};
  
  // スキーマの絶対パスを取得
  const absolutePath = schemaPath.startsWith('/') 
    ? schemaPath 
    : pathUtils.join(baseDir, schemaPath);
  
  try {
    // JSONスキーマファイルを読み込む
    const content = await fs.readTextFile(absolutePath);
    const schema = JSON.parse(content);
    
    // 再帰的に$refを解決してバンドル
    return await bundleReferences(schema, absolutePath, schemaCache, fs, pathUtils, baseDir);
  } catch (error: any) {
    throw new Error(`スキーマの読み込みに失敗: ${error.message}`);
  }
}

/**
 * 再帰的に依存関係を見つける
 */
async function findDependencies(
  filePath: string,
  dependencies: DependencyMap,
  visited: Set<string>,
  fs: FileSystem,
  pathUtils: PathUtils,
  baseDir: string,
  refKeywords = DEFAULT_REF_KEYWORDS
): Promise<void> {
  if (visited.has(filePath)) {
    return;
  }
  
  visited.add(filePath);
  dependencies[filePath] = [];
  
  try {
    // JSONスキーマファイルを読み込む
    const content = await fs.readTextFile(filePath);
    const schema = JSON.parse(content);
    
    // $refを再帰的に検索
    await findRefsInObject(
      schema, 
      filePath, 
      dependencies, 
      visited, 
      fs, 
      pathUtils, 
      baseDir, 
      refKeywords
    );
  } catch (error: any) {
    console.error(`${filePath}の処理中にエラー: ${error.message}`);
  }
}

/**
 * オブジェクト内の$refを検索
 */
async function findRefsInObject(
  obj: any,
  basePath: string,
  dependencies: DependencyMap,
  visited: Set<string>,
  fs: FileSystem,
  pathUtils: PathUtils,
  baseDir: string,
  refKeywords = DEFAULT_REF_KEYWORDS
): Promise<void> {
  if (!obj || typeof obj !== 'object') {
    return;
  }
  
  if (Array.isArray(obj)) {
    for (const item of obj) {
      await findRefsInObject(
        item, 
        basePath, 
        dependencies, 
        visited, 
        fs, 
        pathUtils, 
        baseDir, 
        refKeywords
      );
    }
    return;
  }
  
  for (const [key, value] of Object.entries(obj)) {
    if (refKeywords.includes(key) && typeof value === 'string') {
      const refPath = value.startsWith('./') 
        ? pathUtils.join(pathUtils.dirname(basePath), value)
        : value.startsWith('/') 
          ? value 
          : pathUtils.join(baseDir, value);
      
      // 依存関係を追加
      if (!dependencies[basePath].includes(refPath)) {
        dependencies[basePath].push(refPath);
      }
      
      // 参照先も再帰的に処理
      await findDependencies(
        refPath, 
        dependencies, 
        visited, 
        fs, 
        pathUtils, 
        baseDir, 
        refKeywords
      );
    } else if (typeof value === 'object' && value !== null) {
      await findRefsInObject(
        value, 
        basePath, 
        dependencies, 
        visited, 
        fs, 
        pathUtils, 
        baseDir, 
        refKeywords
      );
    }
  }
}

/**
 * $refを再帰的に解決する
 */
async function bundleReferences(
  obj: any,
  basePath: string,
  cache: SchemaCache,
  fs: FileSystem,
  pathUtils: PathUtils,
  baseDir: string
): Promise<any> {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }
  
  // 配列の場合、各要素に対して再帰的に解決
  if (Array.isArray(obj)) {
    const result = [];
    for (let i = 0; i < obj.length; i++) {
      result[i] = await bundleReferences(obj[i], basePath, cache, fs, pathUtils, baseDir);
    }
    return result;
  }
  
  // $refが含まれているかチェック
  if (obj.$ref && typeof obj.$ref === 'string') {
    const refPath = obj.$ref.startsWith('./') 
      ? pathUtils.join(pathUtils.dirname(basePath), obj.$ref)
      : obj.$ref.startsWith('/') 
        ? obj.$ref 
        : pathUtils.join(baseDir, obj.$ref);
    
    // キャッシュをチェック
    if (!cache[refPath]) {
      try {
        const refContent = await fs.readTextFile(refPath);
        const refSchema = JSON.parse(refContent);
        // キャッシュに格納
        cache[refPath] = refSchema;
      } catch (error: any) {
        throw new Error(`参照の解決に失敗 (${obj.$ref}): ${error.message}`);
      }
    }
    
    // インラインで参照を展開せず、そのまま返す
    return obj;
  }
  
  // 新しいオブジェクトを作成して結果を格納
  const result: Record<string, any> = {};
  
  // 全てのプロパティを処理
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'object' && value !== null) {
      // オブジェクトの場合、再帰的に解決
      result[key] = await bundleReferences(value, basePath, cache, fs, pathUtils, baseDir);
    } else {
      // その他の値はそのままコピー
      result[key] = value;
    }
  }
  
  return result;
}
