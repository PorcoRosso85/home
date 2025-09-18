/**
 * graphBuilder.ts
 * 
 * 依存関係をグラフ構造として構築するための純粋関数群
 * クリーンアーキテクチャのドメイン層に位置する
 */

import { TypeDependency } from "./referenceAnalyzer.ts";
import { Graph, Node, Edge, createGraph, createNode, createEdge, addNode, addEdge, findNodeById } from "../entities/graph.ts";

/**
 * 依存関係ツリーからグラフ構造へ変換する
 * 
 * @param tree 型依存関係のツリー構造
 * @returns グラフ構造
 */
export function dependencyTreeToGraph(tree: TypeDependency): Graph {
  // 初期グラフを作成
  let graph = createGraph();
  
  // 再帰的に依存関係ツリーからグラフを構築（重複ノード検出機能付き）
  const processedNodes = new Set<string>();
  return buildGraphFromTreeImproved(graph, tree, null, processedNodes);
}

/**
 * 再帰的に依存関係ツリーからグラフを構築する内部関数（改善版）
 * - 重複ノード検出と循環参照検出機能を強化
 * 
 * @param graph 現在のグラフ
 * @param dependency 現在処理中の依存関係
 * @param parentId 親ノードのID（ルートの場合はnull）
 * @param processedNodes 既に処理済みのノードID集合（重複防止用）
 * @returns 更新されたグラフ
 */
function buildGraphFromTreeImproved(
  graph: Graph, 
  dependency: TypeDependency, 
  parentId: string | null, 
  processedNodes: Set<string>
): Graph {
  // 既に処理済みのノードかどうかチェック
  if (processedNodes.has(dependency.name)) {
    // ノードは既に存在するので、エッジのみ追加
    if (parentId !== null) {
      const edgeId = `${parentId}_to_${dependency.name}`;
      // エッジが既に存在しないことを確認
      if (!graph.edges.some(edge => edge.id === edgeId)) {
        const edge = createEdge(
          edgeId,
          parentId,
          dependency.name,
          "depends_on",
          { type: "reused_dependency" } // 重複依存を示すプロパティを追加
        );
        graph = addEdge(graph, edge);
      }
    }
    return graph;
  }
  
  // 新しいノードを処理済みとしてマーク
  processedNodes.add(dependency.name);
  
  // ノードを作成
  const node = createNode(
    dependency.name,
    [dependency.metaSchema],
    {
      path: dependency.path || "",
      description: ""
    }
  );
  
  // グラフにノードを追加
  graph = addNode(graph, node);
  
  // 親ノードとの依存関係エッジを追加（ルートノード以外の場合）
  if (parentId !== null) {
    const edgeId = `${parentId}_to_${dependency.name}`;
    const edge = createEdge(
      edgeId,
      parentId,
      dependency.name,
      "depends_on",
      {}
    );
    graph = addEdge(graph, edge);
  }
  
  // 子依存関係を再帰的に処理
  if (dependency.dependencies && dependency.dependencies.length > 0) {
    for (const childDep of dependency.dependencies) {
      graph = buildGraphFromTreeImproved(graph, childDep, dependency.name, processedNodes);
    }
  }
  
  return graph;
}

/**
 * JSONスキーマから$ref属性を抽出し、グラフ構造を構築する（改善版）
 * - 循環参照と重複ノードの検出機能強化
 * - ノードID生成方法の改善
 * 
 * @param schema JSONスキーマオブジェクト
 * @param baseNodeId ベースノードのID（オプション）
 * @returns 依存関係グラフ
 */
export function buildDependencyGraph(schema: unknown, baseNodeId: string = "root"): Graph {
  // 初期グラフを作成
  let graph = createGraph();
  
  // ルートノードを作成
  const rootNode = createNode(baseNodeId, ["rootSchema"], {
    type: "schema",
    title: (schema as any)?.title || "Unknown Schema",
    isRoot: true
  });
  graph = addNode(graph, rootNode);
  
  // $ref属性を収集しグラフに追加
  const visitedRefs = new Set<string>();
  const processedNodePaths = new Map<string, string>(); // パスからノードIDへのマッピング
  
  // 改善されたメソッドでグラフを構築
  graph = collectReferencesRecursiveImproved(graph, schema, baseNodeId, visitedRefs, processedNodePaths, "");
  
  return graph;
}

/**
 * オブジェクト内の$ref属性を再帰的に収集し、グラフに追加する（改善版）
 * 
 * @param graph 現在のグラフ
 * @param obj 検索対象のオブジェクト
 * @param parentId 親ノードのID
 * @param visitedRefs 訪問済みの参照セット（循環参照防止）
 * @param processedNodePaths すでに処理済みのノードパス→ID変換マップ（重複ノード防止）
 * @param currentPath 現在の処理パス
 * @returns 更新されたグラフ
 */
function collectReferencesRecursiveImproved(
  graph: Graph, 
  obj: unknown, 
  parentId: string, 
  visitedRefs: Set<string>,
  processedNodePaths: Map<string, string>,
  currentPath: string
): Graph {
  // null、undefined、または基本型の場合は処理しない
  if (obj === null || typeof obj !== "object") {
    return graph;
  }
  
  // 配列の場合は各要素を再帰的に処理
  if (Array.isArray(obj)) {
    for (let i = 0; i < obj.length; i++) {
      const itemPath = `${currentPath}[${i}]`;
      graph = collectReferencesRecursiveImproved(graph, obj[i], parentId, visitedRefs, processedNodePaths, itemPath);
    }
    return graph;
  }
  
  // FIXME: ルートレベルのexternalDependenciesを特別に処理
  // E2Eテスト中に特定された問題: 外部依存関係が検出されていない
  // externalDependencies配列を検出して直接処理する
  if (currentPath === '' && (obj as any).externalDependencies && Array.isArray((obj as any).externalDependencies)) {
    const extDeps = (obj as any).externalDependencies;
    for (let i = 0; i < extDeps.length; i++) {
      const dep = extDeps[i];
      if (dep.$ref && typeof dep.$ref === 'string') {
        // 参照から識別子を抽出
        const refId = extractRefId(dep.$ref);
        
        // 参照ノードがまだグラフに存在しない場合は作成
        if (!graph.nodes.some(node => node.id === refId)) {
          const refNode = createNode(refId, ["external_dependency"], {
            refPath: dep.$ref,
            description: dep.description || "",
            isExternalDependency: true
          });
          graph = addNode(graph, refNode);
        }
        
        // 親ノードから参照ノードへのエッジを追加
        const edgeId = `${parentId}_extdep_${refId}`;
        if (!graph.edges.some(edge => edge.id === edgeId)) {
          const edge = createEdge(
            edgeId,
            parentId,
            refId,
            "external_dependency",
            { 
              isExternalDependency: true,
              description: dep.description || "",
              path: `externalDependencies[${i}].$ref`
            }
          );
          graph = addEdge(graph, edge);
        }
      }
    }
  }
  
  // オブジェクトのプロパティを反復処理
  for (const [key, value] of Object.entries(obj)) {
    const propertyPath = currentPath ? `${currentPath}.${key}` : key;
    
    // $ref属性を検出した場合はグラフに追加
    if (key === "$ref" && typeof value === "string") {
      const refPath = value as string;
      
      // 参照から識別子を抽出
      const refId = extractRefId(refPath);
      
      // 循環参照チェック - パスによる訪問追跡
      const refVisitKey = `${parentId}:${refPath}`;
      const isCyclicRef = visitedRefs.has(refVisitKey);
      visitedRefs.add(refVisitKey);
      
      // 参照ノードがまだグラフに存在しない場合は作成
      if (!graph.nodes.some(node => node.id === refId)) {
        const refNode = createNode(refId, ["reference"], {
          refPath: refPath,
          isCircular: isCyclicRef
        });
        graph = addNode(graph, refNode);
      } else if (isCyclicRef) {
        // 既存ノードを循環参照としてマーク
        const existingNode = findNodeById(graph, refId);
        if (existingNode) {
          const updatedNode = {
            ...existingNode,
            properties: {
              ...existingNode.properties,
              isCircular: true
            }
          };
          // 既存ノードを更新（イミュータブルな方法で）
          graph = {
            nodes: graph.nodes.map(n => n.id === refId ? updatedNode : n),
            edges: [...graph.edges]
          };
        }
      }
      
      // 親ノードから参照ノードへのエッジを追加
      const edgeId = `${parentId}_to_${refId}`;
      if (!graph.edges.some(edge => edge.id === edgeId)) {
        const edge = createEdge(
          edgeId,
          parentId,
          refId,
          "references",
          { 
            property: key,
            path: propertyPath,
            isCircular: isCyclicRef
          }
        );
        graph = addEdge(graph, edge);
      }
    }
    
    // オブジェクトや配列の場合は再帰的に処理
    if (value !== null && typeof value === "object") {
      // 子オブジェクト用の適切なノードIDを生成
      const childId = processedNodePaths.get(propertyPath) || `${parentId}_${key}`;
      
      // このパスがまだ処理されていない場合、マップに追加
      if (!processedNodePaths.has(propertyPath)) {
        processedNodePaths.set(propertyPath, childId);
      }
      
      // 再帰的に処理（常に適切な親IDを使用）
      graph = collectReferencesRecursiveImproved(
        graph, 
        value, 
        childId, 
        visitedRefs, 
        processedNodePaths,
        propertyPath
      );
    }
  }
  
  return graph;
}

/**
 * 参照パスから識別子を抽出する（改善版）
 * - より明確なノードID命名規則
 * 
 * @param refPath 参照パス（例: "#/definitions/TypeName"）
 * @returns 抽出された識別子（例: "TypeName"）
 */
function extractRefId(refPath: string): string {
  // ローカル参照（例: "#/definitions/TypeName"）
  if (refPath.startsWith("#/")) {
    const parts = refPath.split("/");
    // 定義部分を識別しやすくする
    if (parts.length >= 3 && parts[1] === "definitions") {
      return parts[parts.length - 1];
    }
    return parts[parts.length - 1];
  }
  
  // 外部参照（例: "other-schema.json#/definitions/TypeName"）
  if (refPath.includes("#/")) {
    const hashParts = refPath.split("#/");
    const fileName = hashParts[0].split("/").pop() || "";
    const typeName = hashParts[1].split("/").pop() || "";
    return `${fileName.replace(/\.json$/, "")}_${typeName}`;
  }
  
  // ファイル名だけの参照（例: "UserRegister__Function.json"）
  const fileNameMatch = refPath.match(/^(.+)__Function\.json$/);
  if (fileNameMatch) {
    return fileNameMatch[1];  // UserRegister 部分を抽出
  }
  
  // フォールバック：参照パス全体を識別子として使用（特殊文字置換）
  return refPath.replace(/[^a-zA-Z0-9_]/g, "_");
}

// ===== In-source テスト =====
// このコードは実運用環境では自動的にスキップされます

if (import.meta.main) {
  console.log("=== graphBuilder_improved.ts の単体テスト実行 ===");

  // テスト1: $refを含むシンプルなスキーマからの依存関係検出テスト
  const testSchema = {
    "title": "TestSchema",
    "type": "object",
    "properties": {
      "prop1": { "$ref": "#/definitions/Type1" },
      "prop2": { "$ref": "#/definitions/Type2" }
    },
    "definitions": {
      "Type1": {
        "type": "object",
        "properties": {
          "field1": { "type": "string" },
          "dependency": { "$ref": "#/definitions/Type2" }
        }
      },
      "Type2": {
        "type": "object",
        "properties": {
          "field2": { "type": "number" }
        }
      }
    }
  };

  // buildDependencyGraph関数のテスト
  console.log("テスト1: buildDependencyGraph - 基本的な依存関係");
  const graph = buildDependencyGraph(testSchema, "TestSchema");
  console.log(`ノード数: ${graph.nodes.length}, エッジ数: ${graph.edges.length}`);
  console.log("ノード:", graph.nodes.map(n => n.id));
  console.log("エッジ:", graph.edges.map(e => `${e.source} -> ${e.target}`));

  // 期待結果: 少なくとも3つのノード (TestSchema, Type1, Type2) と少なくとも2つのエッジ
  const expectedNodeCount = 3;
  const expectedMinEdgeCount = 2;
  console.log(`テスト結果: ${graph.nodes.length >= expectedNodeCount && graph.edges.length >= expectedMinEdgeCount ? '成功' : '失敗'}`);

  // テスト2: 深くネストされた$refの検出テスト
  const nestedTestSchema = {
    "title": "NestedSchema",
    "type": "object",
    "properties": {
      "level1": {
        "type": "object",
        "properties": {
          "level2": {
            "type": "object",
            "properties": {
              "level3": {
                "$ref": "#/definitions/DeepType"
              }
            }
          }
        }
      }
    },
    "definitions": {
      "DeepType": {
        "type": "object",
        "properties": {
          "value": { "type": "string" }
        }
      }
    }
  };

  console.log("\nテスト2: ネストされた$refの検出");
  const nestedGraph = buildDependencyGraph(nestedTestSchema, "NestedSchema");
  console.log(`ノード数: ${nestedGraph.nodes.length}, エッジ数: ${nestedGraph.edges.length}`);
  console.log("ノード:", nestedGraph.nodes.map(n => n.id));
  console.log("エッジ:", nestedGraph.edges.map(e => `${e.source} -> ${e.target}`));

  // 期待結果: 参照がネストの深くから検出されること
  const containsDeepType = nestedGraph.nodes.some(n => n.id === "DeepType");
  console.log(`テスト結果: ${containsDeepType ? '成功' : '失敗'}`);
  
  // テスト3: 循環参照の検出テスト
  const cyclicTestSchema = {
    "title": "CyclicSchema",
    "type": "object",
    "properties": {
      "circularA": { "$ref": "#/definitions/TypeA" }
    },
    "definitions": {
      "TypeA": {
        "type": "object",
        "properties": {
          "refToB": { "$ref": "#/definitions/TypeB" }
        }
      },
      "TypeB": {
        "type": "object",
        "properties": {
          "refBackToA": { "$ref": "#/definitions/TypeA" }
        }
      }
    }
  };

  console.log("\nテスト3: 循環参照の検出");
  const cyclicGraph = buildDependencyGraph(cyclicTestSchema, "CyclicSchema");
  console.log(`ノード数: ${cyclicGraph.nodes.length}, エッジ数: ${cyclicGraph.edges.length}`);
  console.log("ノード:", cyclicGraph.nodes.map(n => n.id));
  console.log("エッジ:", cyclicGraph.edges.map(e => `${e.source} -> ${e.target} (循環: ${(e.properties as any).isCircular ? 'はい' : 'いいえ'})`));

  // 期待結果: 循環参照が検出され、適切にマークされていること
  const hasCyclicRef = cyclicGraph.edges.some(edge => (edge.properties as any).isCircular === true);
  console.log(`テスト結果: ${hasCyclicRef ? '成功' : '失敗'}`);
  
  // テスト4: 重複ノードの統合テスト
  const duplicateTestSchema = {
    "title": "DuplicateSchema",
    "type": "object",
    "properties": {
      "ref1": { "$ref": "#/definitions/SharedType" },
      "ref2": { "$ref": "#/definitions/SharedType" },
      "nested": {
        "type": "object",
        "properties": {
          "ref3": { "$ref": "#/definitions/SharedType" }
        }
      }
    },
    "definitions": {
      "SharedType": {
        "type": "object",
        "properties": {
          "value": { "type": "string" }
        }
      }
    }
  };

  console.log("\nテスト4: 重複ノードの統合");
  const duplicateGraph = buildDependencyGraph(duplicateTestSchema, "DuplicateSchema");
  console.log(`ノード数: ${duplicateGraph.nodes.length}, エッジ数: ${duplicateGraph.edges.length}`);
  console.log("ノード:", duplicateGraph.nodes.map(n => n.id));
  console.log("SharedTypeへのエッジ数:", duplicateGraph.edges.filter(e => e.target === "SharedType").length);

  // 期待結果: 重複参照でもSharedTypeノードは1つだけ存在すること
  const sharedTypeCount = duplicateGraph.nodes.filter(n => n.id === "SharedType").length;
  const sharedTypeEdges = duplicateGraph.edges.filter(e => e.target === "SharedType").length;
  console.log(`テスト結果: ${sharedTypeCount === 1 && sharedTypeEdges > 1 ? '成功' : '失敗'}`);
  
  // テスト5: 外部依存関係（ファイル名参照）の検出
  const externalDepsTest = {
    "title": "ExternalDepsTest",
    "externalDependencies": [
      {
        "$ref": "UserRegister__Function.json",
        "description": "Test dependency"
      }
    ]
  };

  console.log("\nテスト5: 外部依存関係（ファイル名参照）の検出");
  const externalGraph = buildDependencyGraph(externalDepsTest, "ExternalDepsTest");
  console.log(`ノード数: ${externalGraph.nodes.length}, エッジ数: ${externalGraph.edges.length}`);
  console.log("ノード:", externalGraph.nodes.map(n => n.id));
  console.log("エッジ:", externalGraph.edges.map(e => `${e.source} -> ${e.target}`));

  // 期待結果: UserRegister ノードと依存関係エッジが検出される
  const hasExternalNode = externalGraph.nodes.some(n => n.id === "UserRegister");
  const hasExternalEdge = externalGraph.edges.some(e => e.target === "UserRegister");
  console.log(`テスト結果: ${hasExternalNode && hasExternalEdge ? '成功' : '失敗'}`);
  
  console.log("\n=== テスト完了 ===");
}
