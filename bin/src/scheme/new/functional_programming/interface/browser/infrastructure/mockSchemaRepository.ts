/**
 * mockSchemaRepository.ts
 * 
 * メモリ上でモックスキーマデータを生成するリポジトリ実装
 */

import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';
import { Graph } from '/home/nixos/scheme/new/functional_programming/domain/entities/graph.ts';
import { SchemaRepository } from '../domain/repository/schemaRepository.ts';

/**
 * モックスキーマデータ
 */
const MOCK_SCHEMAS: FunctionSchema[] = [
  {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: "UserRegister",
    description: "ユーザー登録のための関数スキーマ",
    type: "object",
    required: ["email", "password", "username"],
    resourceUri: "file:///home/nixos/scheme/new/functional_programming/schemas/user/UserRegister.json",
    properties: {
      email: {
        type: "string",
        format: "email",
        description: "ユーザーのメールアドレス"
      },
      password: {
        type: "string",
        minLength: 8,
        description: "ユーザーのパスワード（8文字以上）"
      },
      username: {
        type: "string",
        minLength: 3,
        description: "ユーザー名（3文字以上）"
      },
      firstName: {
        type: "string",
        description: "ユーザーの名（オプション）"
      },
      lastName: {
        type: "string",
        description: "ユーザーの姓（オプション）"
      }
    }
  },
  {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: "UserAuthenticate",
    description: "ユーザー認証のための関数スキーマ",
    type: "object",
    required: ["email", "password"],
    resourceUri: "file:///home/nixos/scheme/new/functional_programming/schemas/user/UserAuthenticate.json",
    properties: {
      email: {
        type: "string",
        format: "email",
        description: "ユーザーのメールアドレス"
      },
      password: {
        type: "string",
        description: "ユーザーのパスワード"
      }
    }
  },
  {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: "CreatePost",
    description: "投稿作成のための関数スキーマ",
    type: "object",
    required: ["userId", "title", "content"],
    resourceUri: "file:///home/nixos/scheme/new/functional_programming/schemas/post/CreatePost.json",
    properties: {
      userId: {
        type: "string",
        description: "投稿者のユーザーID"
      },
      title: {
        type: "string",
        minLength: 5,
        description: "投稿のタイトル（5文字以上）"
      },
      content: {
        type: "string",
        minLength: 10,
        description: "投稿の本文（10文字以上）"
      },
      tags: {
        type: "array",
        items: {
          type: "string"
        },
        description: "関連タグのリスト（オプション）"
      }
    }
  },
  {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: "GetPost",
    description: "投稿取得のための関数スキーマ",
    type: "object",
    required: ["postId"],
    resourceUri: "file:///home/nixos/scheme/new/functional_programming/schemas/post/GetPost.json",
    properties: {
      postId: {
        type: "string",
        description: "取得する投稿のID"
      },
      includeComments: {
        type: "boolean",
        default: false,
        description: "コメントを含めるかどうか（デフォルト: false）"
      }
    }
  },
  {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: "CreateComment",
    description: "コメント作成のための関数スキーマ",
    type: "object",
    required: ["postId", "userId", "content"],
    resourceUri: "file:///home/nixos/scheme/new/functional_programming/schemas/comment/CreateComment.json",
    properties: {
      postId: {
        type: "string",
        description: "コメント対象の投稿ID"
      },
      userId: {
        type: "string",
        description: "コメント投稿者のユーザーID"
      },
      content: {
        type: "string",
        minLength: 1,
        description: "コメントの内容（1文字以上）"
      },
      parentCommentId: {
        type: "string",
        description: "親コメントのID（返信の場合、オプション）"
      }
    }
  }
];

/**
 * モック依存関係グラフ
 */
const MOCK_GRAPH: Graph = {
  nodes: MOCK_SCHEMAS.map(schema => ({
    id: schema.title,
    labels: [schema.type],
    properties: {
      type: schema.type,
      description: schema.description
    }
  })),
  edges: [
    {
      id: "edge1",
      source: "UserRegister",
      target: "UserAuthenticate",
      label: "関連",
      properties: {
        isCircular: false
      }
    },
    {
      id: "edge2",
      source: "CreatePost",
      target: "UserAuthenticate",
      label: "依存",
      properties: {
        isCircular: false
      }
    },
    {
      id: "edge3",
      source: "GetPost",
      target: "CreatePost",
      label: "関連",
      properties: {
        isCircular: false
      }
    },
    {
      id: "edge4",
      source: "CreateComment",
      target: "GetPost",
      label: "依存",
      properties: {
        isCircular: false
      }
    },
    {
      id: "edge5",
      source: "CreateComment",
      target: "UserAuthenticate",
      label: "依存",
      properties: {
        isCircular: false
      }
    }
  ]
};

/**
 * モックスキーマリポジトリ実装
 */
export class MockSchemaRepository implements SchemaRepository {
  private schemas: FunctionSchema[] = MOCK_SCHEMAS;
  private graph: Graph = MOCK_GRAPH;

  /**
   * 利用可能なスキーマのパスリストを取得
   */
  async getSchemaList(): Promise<string[]> {
    return this.schemas.map(schema => schema.resourceUri || '');
  }
  
  /**
   * 指定したパスのスキーマを取得
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    const schema = this.schemas.find(s => s.resourceUri === path);
    if (!schema) {
      throw new Error(`スキーマが見つかりません: ${path}`);
    }
    return schema;
  }

  /**
   * すべてのスキーマを取得
   */
  async getAllSchemas(): Promise<FunctionSchema[]> {
    return [...this.schemas];
  }
  
  /**
   * 依存関係グラフを取得
   */
  async getDependencyGraph(_rootSchemaPath: string): Promise<Graph> {
    return this.graph;
  }
}
