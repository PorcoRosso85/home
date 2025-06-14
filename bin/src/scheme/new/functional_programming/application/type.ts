/**
 * type.ts
 * 
 * CLI、サーバー、ブラウザの各インターフェースで共通して使用する型定義
 * 各インターフェース固有のデータモデルを共通のドメインオブジェクトに変換するための
 * アダプターパターンを実装します。
 */

import { FunctionSchema } from '../domain/schema.ts';
import { Graph, Node, Edge } from '../domain/entities/graph.ts';
import { TypeDefinition } from '../domain/typeDefinitions.ts';

/**
 * アプリケーション間で共通するコマンド引数の型
 */
export interface CommandArgs {
  /** コマンド名 */
  command: string;
  /** 入力ファイルパス */
  input?: string;
  /** 出力ファイルパス */
  output?: string;
  /** フラグ引数 */
  flags: Record<string, boolean>;
  /** 値引数 */
  options: Record<string, string>;
  /** その他の引数 */
  args: string[];
}

/**
 * コマンドライン引数からCommandArgs型への変換関数
 * 
 * @param args コマンドライン引数の配列
 * @returns CommandArgs オブジェクト
 */
export function parseCommandLineArgs(args: string[]): CommandArgs {
  const result: CommandArgs = {
    command: '',
    flags: {},
    options: {},
    args: []
  };

  // 最初の引数はコマンド名
  if (args.length > 0) {
    result.command = args[0];
  }

  // 残りの引数を解析
  for (let i = 1; i < args.length; i++) {
    const arg = args[i];

    // フラグ引数 (--flag または -f 形式)
    if (arg.startsWith('--')) {
      const flag = arg.substring(2);
      result.flags[flag] = true;
    }
    else if (arg.startsWith('-') && arg.length > 1) {
      const flag = arg.substring(1);
      result.flags[flag] = true;
    }
    // オプション引数 (--key=value 形式)
    else if (arg.includes('=') && arg.startsWith('--')) {
      const [key, value] = arg.substring(2).split('=', 2);
      result.options[key] = value;
    }
    // 入力ファイル引数
    else if (!result.input && (arg.endsWith('.json') || arg.endsWith('.ts'))) {
      result.input = arg;
    }
    // 出力ファイル引数
    else if (!result.output && i > 0 && args[i-1] === '-o') {
      result.output = arg;
    }
    // その他の引数
    else {
      result.args.push(arg);
    }
  }

  return result;
}

/**
 * APIリクエストボディの共通型
 */
export interface ApiRequest {
  /** アクション (動作種別) */
  action: string;
  /** ファイルパス */
  filePath?: string;
  /** データオブジェクト */
  data?: any;
  /** オプション */
  options?: Record<string, any>;
}

/**
 * APIレスポンスの共通型
 */
export interface ApiResponse {
  /** 成功したかどうか */
  success: boolean;
  /** メッセージ */
  message?: string;
  /** データオブジェクト */
  data?: any;
  /** エラー情報 */
  error?: any;
}

/**
 * スキーマデータアクセスインターフェース
 * 異なるインターフェース（CLI、サーバー、ブラウザ）でのデータアクセスを抽象化
 */
export interface SchemaDataAccess {
  /** スキーマのロード */
  loadSchema(path: string): Promise<FunctionSchema>;
  /** スキーマの保存 */
  saveSchema(schema: FunctionSchema, path: string): Promise<void>;
  /** 依存関係グラフの取得 */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
  /** スキーマの検証 */
  validateSchema(schema: FunctionSchema): Promise<boolean>;
}

/**
 * クライアント側でのブラウザAPIクライアント
 */
export interface BrowserApiClient {
  /** スキーマロード */
  loadSchema(path: string): Promise<FunctionSchema>;
  /** 依存関係グラフの取得 */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
  /** スキーマリストの取得 */
  getSchemaList(): Promise<string[]>;
}

/**
 * 関数データのメタ情報
 */
export interface FunctionData {
  /** 関数のフルパス (file/path.ts:::functionName 形式) */
  path: string;
  /** メタデータ */
  metadata: {
    /** 説明 */
    description: string;
    /** 戻り値の型 */
    returnType: string;
    /** パラメータの配列 */
    parameters: string[];
    /** その他のプロパティ */
    [key: string]: any;
  };
}

/**
 * JSON文字列からFunctionSchemaオブジェクトへの変換
 * 
 * @param json JSON文字列
 * @returns FunctionSchema オブジェクト
 */
export function parseFunctionSchema(json: string): FunctionSchema {
  try {
    return JSON.parse(json) as FunctionSchema;
  } catch (error) {
    throw new Error(`スキーマJSONの解析に失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * FunctionDataオブジェクトからFunctionSchemaオブジェクトへの変換
 * 
 * @param data FunctionData オブジェクト
 * @returns FunctionSchema オブジェクト
 */
export function functionDataToSchema(data: FunctionData): FunctionSchema {
  const [filePath, funcName] = data.path.split(':::');
  
  // 基本スキーマを生成
  const schema: FunctionSchema = {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    title: funcName || "未命名関数",
    description: data.metadata.description || "",
    type: "object",
    required: ["title", "type", "signatures"],
    properties: {
      title: {
        type: "string",
        description: "関数型の名前"
      },
      description: {
        type: "string",
        description: "関数型の説明"
      },
      type: {
        type: "string",
        enum: ["function"],
        description: "型のカテゴリ (関数のため 'function'固定)"
      },
      resourceUri: {
        type: "string",
        description: "関数の実装リソースURI",
        pattern: "^file:///.+$",
        default: `file:///${filePath}`
      },
      signatures: {
        type: "array",
        description: "関数のシグネチャ（引数型と戻り値型のペア）リスト",
        minItems: 1,
        items: {
          type: "object",
          required: ["id", "parameterTypes", "returnType"],
          properties: {
            id: {
              type: "string",
              description: "シグネチャの識別子",
              default: "main"
            },
            description: {
              type: "string",
              description: "シグネチャの説明",
              default: data.metadata.description || ""
            },
            parameterTypes: {
              type: "object",
              description: "関数の入力パラメータの型",
              // パラメータに基づいた動的な型定義を生成
              properties: data.metadata.parameters.reduce((acc, param, index) => {
                acc[param] = {
                  type: "string",
                  description: `パラメータ ${param} の説明`
                };
                return acc;
              }, {} as Record<string, any>)
            },
            returnType: {
              type: "object",
              description: "関数の戻り値の型",
              required: ["type"],
              properties: {
                type: {
                  type: "string",
                  description: "戻り値の型",
                  default: data.metadata.returnType || "any"
                },
                description: {
                  type: "string",
                  description: "戻り値の説明"
                }
              }
            }
          }
        }
      }
    }
  };
  
  return schema;
}

/**
 * FunctionSchema のリストから Graph オブジェクトを生成
 * 
 * @param schemas FunctionSchema オブジェクトの配列
 * @returns Graph オブジェクト
 */
export function schemasToGraph(schemas: FunctionSchema[]): Graph {
  const graph: Graph = {
    nodes: [],
    edges: []
  };
  
  // ノードIDのマップ (重複回避用)
  const nodeIds = new Set<string>();
  
  // 各スキーマをノードとして追加
  for (const schema of schemas) {
    const nodeId = `${schema.title}`;
    
    // 重複ノードをスキップ
    if (nodeIds.has(nodeId)) continue;
    nodeIds.add(nodeId);
    
    // ノードを追加
    graph.nodes.push({
      id: nodeId,
      labels: ['Function'],
      properties: {
        title: schema.title,
        description: schema.description,
        type: schema.type,
        resourceUri: schema.properties.resourceUri?.default || ''
      }
    });
    
    // 依存関係を検出してエッジを追加
    // $refプロパティを探索して参照を抽出
    const refs = findReferences(schema);
    for (const ref of refs) {
      const targetId = extractTargetFromRef(ref);
      if (targetId && targetId !== nodeId) {
        // エッジを追加
        graph.edges.push({
          id: `${nodeId}->${targetId}`,
          source: nodeId,
          target: targetId,
          label: 'references',
          properties: {}
        });
      }
    }
  }
  
  return graph;
}

/**
 * スキーマオブジェクトから$refの参照を抽出
 * 
 * @param obj 探索対象のオブジェクト
 * @returns 見つかった$refの値の配列
 */
function findReferences(obj: any): string[] {
  const refs: string[] = [];
  
  // オブジェクトの再帰的探索関数
  function explore(value: any) {
    if (!value || typeof value !== 'object') return;
    
    // 配列の場合は各要素を探索
    if (Array.isArray(value)) {
      for (const item of value) {
        explore(item);
      }
      return;
    }
    
    // $refプロパティがあれば追加
    if ('$ref' in value && typeof value.$ref === 'string') {
      refs.push(value.$ref);
    }
    
    // 他のプロパティを再帰的に探索
    for (const key in value) {
      explore(value[key]);
    }
  }
  
  explore(obj);
  return refs;
}

/**
 * $ref値からターゲットID（スキーマ名など）を抽出
 * 
 * @param ref $refの値
 * @returns 抽出されたターゲットID、抽出できない場合はnull
 */
function extractTargetFromRef(ref: string): string | null {
  // 一般的なパターン: "#/definitions/XXX" や "#/$defs/XXX"
  const defMatch = ref.match(/#\/(?:definitions|$defs)\/([^/]+)/);
  if (defMatch) return defMatch[1];
  
  // scheme://type/source:id 形式
  const schemeMatch = ref.match(/scheme:\/\/([^/]+)\/[^:]+:(.+)/);
  if (schemeMatch) return schemeMatch[2];
  
  // file:// 形式
  const fileMatch = ref.match(/file:\/\/\/(.+)/);
  if (fileMatch) {
    // ファイルパスから最後の部分を抽出
    const parts = fileMatch[1].split('/');
    return parts[parts.length - 1].replace(/\.[^.]+$/, '');
  }
  
  return null;
}
