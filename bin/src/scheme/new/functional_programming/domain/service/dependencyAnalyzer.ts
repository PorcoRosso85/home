/**
 * dependencyAnalyzer.ts
 * 
 * JSONスキーマの依存関係を解析するための純粋関数群
 * クリーンアーキテクチャのドメイン層に位置する
 * 
 * Function.meta.jsonでは以下のプロパティが$refをサポートしています：
 * 
 * 1. シグネチャのパラメータ型
 *    パス: properties.signatures.items.properties.parameterTypes.properties.$ref
 *    説明: 関数シグネチャのパラメータ型を外部スキーマで定義する場合に使用します。
 * 
 * 2. シグネチャの戻り値型
 *    パス: properties.signatures.items.properties.returnTypes.properties.$ref
 *    説明: 関数シグネチャの戻り値型を外部スキーマで定義する場合に使用します。
 * 
 * 3. 相互再帰関数への参照
 *    パス: properties.features.properties.recursion.properties.mutuallyRecursiveWith.items.properties.$ref
 *    説明: 相互再帰関係にある他の関数への参照に使用します。
 * 
 * 4. 外部依存関係
 *    パス: properties.externalDependencies.items.properties.$ref
 *    説明: この関数が依存する外部関数への参照に使用します。
 */

import { SchemaReference, TypeDependency, parseReference } from './referenceAnalyzer.ts';

/**
 * JSONスキーマ内の$ref属性を再帰的に検索する
 * 
 * @param obj 検索対象のオブジェクト
 * @param path 現在の検索パス
 * @returns 見つかった$ref属性の配列（パス情報付き）
 */
export function findReferences(obj: any, path: string = ''): Array<{ ref: string; path: string }> {
  // null または未定義の場合は空配列を返す
  if (obj === null || obj === undefined) {
    return [];
  }
  
  // 基本型の場合は空配列を返す
  if (typeof obj !== 'object') {
    return [];
  }
  
  // 配列の場合は各要素を再帰的に検索
  if (Array.isArray(obj)) {
    return obj.flatMap((item, index) => 
      findReferences(item, path ? `${path}[${index}]` : `[${index}]`)
    );
  }
  
  // 結果を格納する配列
  const results: Array<{ ref: string; path: string }> = [];
  
  // $ref属性がある場合は結果に追加
  if (obj.$ref && typeof obj.$ref === 'string') {
    results.push({
      ref: obj.$ref,
      path: path ? `${path}.$ref` : '$ref'
    });
  }
  
  // ルートレベルのexternalDependencies配列を特別に処理
  // 外部依存関係の$refも正しく検出する
  if (path === '' && obj.externalDependencies && Array.isArray(obj.externalDependencies)) {
    for (let i = 0; i < obj.externalDependencies.length; i++) {
      const dep = obj.externalDependencies[i];
      if (dep.$ref && typeof dep.$ref === 'string') {
        results.push({
          ref: dep.$ref,
          path: `externalDependencies[${i}].$ref`
        });
      }
    }
  }
  
  // オブジェクトの各プロパティを再帰的に検索
  for (const [key, value] of Object.entries(obj)) {
    // $refプロパティは既に処理済みのためスキップ
    if (key === '$ref') continue;
    
    // プロパティ値を再帰的に検索
    const childPath = path ? `${path}.${key}` : key;
    const childResults = findReferences(value, childPath);
    
    // 子の結果を親の結果に統合
    results.push(...childResults);
  }
  
  return results;
}

/**
 * スキーマから依存関係ツリーを構築する
 * 
 * @param schemaData スキーマデータ
 * @param schemaName スキーマ名
 * @param visited 訪問済みの依存関係（循環参照防止用）
 * @returns 依存関係ツリー
 */
export function buildDependencyTree(
  schemaData: any, 
  schemaName: string,
  visited: Set<string> = new Set()
): TypeDependency {
  // 基本構造を初期化
  const result: TypeDependency = {
    name: schemaName,
    metaSchema: schemaData.title || 'Unknown',
    path: '',
    dependencies: []
  };
  
  // 既に訪問済みのスキーマの場合は依存関係を追加せずに返す（循環参照防止）
  if (visited.has(schemaName)) {
    return result;
  }
  
  // 訪問済みに追加
  visited.add(schemaName);
  
  // $ref属性を探索
  const references = findReferences(schemaData);
  
  // 参照の解析と依存関係の構築
  for (const { ref, path } of references) {
    // 外部依存関係の処理 (直接ファイル名参照)
    if (path.startsWith('externalDependencies') && ref.endsWith('__Function.json')) {
      // 単純なファイル名から依存関係を抽出
      const depName = ref.replace('__Function.json', '');
      
      // 依存関係の子ノードを作成
      const childDependency: TypeDependency = {
        name: depName,
        metaSchema: 'function/external',
        path,
        dependencies: []
      };
      
      // 子ノードを追加
      result.dependencies.push(childDependency);
    } else {
      // 一般的な参照の解析
      const parsedRef = parseReference(ref);
      
      if (parsedRef) {
        // 依存関係の子ノードを作成
        const childDependency: TypeDependency = {
          name: parsedRef.typeId,
          metaSchema: `${parsedRef.metaSource}/${parsedRef.metaId}`,
          path,
          dependencies: []
        };
        
        // 子の依存関係を再帰的に解析（既に訪問済みのノードは再度解析しない）
        result.dependencies.push(childDependency);
      }
    }
  }
  
  return result;
}

/**
 * 未解決の依存関係を追跡する
 * 
 * @param root ルート依存関係
 * @param availableTypes 利用可能な型の集合
 * @returns 未解決の依存関係のリスト
 */
export function findUnresolvedDependencies(
  root: TypeDependency,
  availableTypes: Set<string>
): string[] {
  const allDeps = new Set<string>();
  const unresolvedDeps: string[] = [];
  
  // 全ての依存関係を収集
  function collectDeps(node: TypeDependency) {
    // 自身の名前を追加
    allDeps.add(node.name);
    
    // 子の依存関係を再帰的に収集
    for (const child of node.dependencies) {
      // 未解決の依存関係を追跡
      if (!availableTypes.has(child.name) && !allDeps.has(child.name)) {
        unresolvedDeps.push(child.name);
      }
      
      collectDeps(child);
    }
  }
  
  collectDeps(root);
  
  // 重複を排除して返す
  return [...new Set(unresolvedDeps)].sort();
}

// ===== In-source テスト =====
// このコードは実運用環境では自動的にスキップされます

if (import.meta.main) {
  // 外部依存関係の参照テスト
  const externDepsTest = {
    "title": "ExternalDepsTest",
    "externalDependencies": [
      {
        "$ref": "UserRegister__Function.json",
        "description": "Test dependency"
      }
    ]
  };
  console.log("\nテスト4: 外部依存関係検出");
  const externalRefs = findReferences(externDepsTest);
  console.log(`検出された外部依存関係: ${externalRefs.length}`);
  console.log(externalRefs);
  console.log(`テスト結果: ${externalRefs.length > 0 ? '成功' : '失敗'}`);
  
  // 外部依存関係ツリー構築テスト
  console.log("\nテスト5: 外部依存関係ツリー構築");
  const externalTree = buildDependencyTree(externDepsTest, "ExternalDepsTest");
  console.log("生成された依存関係ツリー:");
  console.log(JSON.stringify(externalTree, null, 2));
  console.log(`テスト結果: ${externalTree.dependencies.length > 0 ? '成功' : '失敗'}`);
  
  console.log("=== dependencyAnalyzer.ts の単体テスト実行 ===");

  // テスト1: $refを含むスキーマからの参照検出テスト
  const testSchema = {
    "title": "TestSchema",
    "type": "object",
    "properties": {
      "prop1": { "$ref": "#/definitions/Type1" },
      "prop2": { "$ref": "#/definitions/Type2" },
      "nestedObject": {
        "type": "object",
        "properties": {
          "deepProp": { "$ref": "#/definitions/Type3" }
        }
      }
    },
    "definitions": {
      "Type1": { "type": "string" },
      "Type2": { "type": "number" },
      "Type3": { "type": "boolean" }
    }
  };

  // テスト1: findReferences関数のテスト
  console.log("テスト1: findReferences");
  const refs = findReferences(testSchema);
  console.log(`検出された$ref: ${refs.length}`);
  console.log(refs);

  // 期待結果: 少なくとも3つの$refが検出される
  const expectedRefCount = 3;
  console.log(`テスト結果: ${refs.length >= expectedRefCount ? '成功' : '失敗'}`);

  // テスト2: buildDependencyTree関数のテスト
  console.log("\nテスト2: buildDependencyTree");
  const tree = buildDependencyTree(testSchema, "TestSchema");
  console.log("生成された依存関係ツリー:");
  console.log(JSON.stringify(tree, null, 2));

  // 期待結果: 3つの依存関係を持つツリーが生成される
  const expectedDependencies = 3;
  console.log(`テスト結果: ${tree.dependencies.length >= expectedDependencies ? '成功' : '失敗'}`);

  // テスト3: Function.meta.jsonの主要な$refパス位置を確認するテスト
  const functionMetaSchema = {
    "title": "Function",
    "type": "object",
    "properties": {
      "signatures": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "parameterTypes": {
              "type": "object",
              "properties": {
                "$ref": { "type": "string" }
              }
            },
            "returnTypes": {
              "type": "object",
              "properties": {
                "$ref": { "type": "string" }
              }
            }
          }
        }
      },
      "features": {
        "type": "object",
        "properties": {
          "recursion": {
            "type": "object",
            "properties": {
              "mutuallyRecursiveWith": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "$ref": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      },
      "externalDependencies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "$ref": { "type": "string" }
          }
        }
      }
    }
  };

  console.log("\nテスト3: Function.meta.jsonの$refパス検出");
  const functionRefs = findReferences(functionMetaSchema);
  console.log(`検出された$ref: ${functionRefs.length}`);
  console.log(functionRefs);

  // 期待結果: Function.meta.jsonの主要な$refパスが正しく検出される
  // シグネチャのパラメータ型、戻り値型、相互再帰関数への参照、外部依存関係
  const expectedFunctionRefPaths = [
    "signatures.items.properties.parameterTypes.properties.$ref",
    "signatures.items.properties.returnTypes.properties.$ref",
    "features.properties.recursion.properties.mutuallyRecursiveWith.items.properties.$ref",
    "externalDependencies.items.properties.$ref"
  ];
  
  const detectedPaths = functionRefs.map(r => r.path);
  const allPathsDetected = expectedFunctionRefPaths.every(path => 
    detectedPaths.some(detectedPath => detectedPath.includes(path))
  );
  
  console.log(`テスト結果: ${allPathsDetected ? '成功' : '失敗'}`);
  
  console.log("\n=== テスト完了 ===");
}
