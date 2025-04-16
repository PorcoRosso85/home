/**
 * 統一要件関連のコマンド処理
 */
import { join } from "https://deno.land/std@0.220.1/path/mod.ts";
import { loadRequirementMetaSchema } from "../cli/cliUtils.ts";

// 統一要件メタスキーマのパス
const REQUIREMENT_META_SCHEMA_PATH = "./data/meta/Requirement.meta.json";

/**
 * 統一要件生成コマンドを実行する
 */
export async function executeRequirementsGeneratorCommand(args: any): Promise<void> {
  const subCommand = args._[1] as string;
  
  if (!subCommand) {
    console.log("統一要件JSONの生成と管理を行うコマンド\n");
    console.log("使用方法: req-gen <コマンド> [オプション] [引数]\n");
    console.log("コマンド:");
    console.log("  create                      新しい統一要件を作成");
    console.log("  convert <要件ID>            既存の要件を統一要件形式に変換");
    console.log("  list                        統一要件一覧を表示");
    console.log("  validate <要件ID>           統一要件を検証\n");
    return;
  }

  // サブコマンドによって処理を分岐
  switch (subCommand) {
    case "create":
      await createRequirement(args);
      break;
    case "convert":
      const requirementId = args._[2] as string;
      
      if (!requirementId) {
        console.error("エラー: 変換する要件IDを指定してください");
        console.log("使用例: cli.ts req-gen convert FileSystemReader");
        Deno.exit(1);
      }
      
      await convertRequirement(requirementId, args);
      break;
    case "list":
      await listRequirements(args.outDir);
      break;
    case "validate":
      const validateId = args._[2] as string;
      
      if (!validateId) {
        console.error("エラー: 検証する要件IDを指定してください");
        console.log("使用例: cli.ts req-gen validate FileSystemReader");
        Deno.exit(1);
      }
      
      await validateRequirement(validateId, args);
      break;
    default:
      console.error(`未知のサブコマンド: ${subCommand}`);
      console.log("使用可能なサブコマンド: create, convert, list, validate");
      Deno.exit(1);
  }
}

/**
 * 新しい統一要件を作成
 * 
 * @param args コマンドライン引数
 */
async function createRequirement(args: any) {
  const id = args._[2] as string;
  
  if (!id) {
    console.error("エラー: 要件IDを指定してください");
    console.log("使用例: cli.ts req-gen create UserManager --title=\"ユーザー管理機能\" --type=struct");
    Deno.exit(1);
  }
  
  // IDの形式チェック
  if (!/^[a-zA-Z0-9-_]+$/.test(id)) {
    console.error("エラー: 要件IDには英数字、ハイフン、アンダースコアのみ使用できます");
    Deno.exit(1);
  }
  
  // 必須パラメータの確認
  if (!args.title) {
    console.error("エラー: --title オプションでタイトルを指定してください");
    Deno.exit(1);
  }
  
  if (!args.type) {
    console.error("エラー: --type オプションで実装タイプを指定してください");
    Deno.exit(1);
  }
  
  // 実装タイプの検証
  const validTypes = ["function", "struct", "string", "enum"];
  if (!validTypes.includes(args.type)) {
    console.error(`エラー: --type オプションは ${validTypes.join(", ")} のいずれかを指定してください`);
    Deno.exit(1);
  }
  
  // 出力パスのデフォルト生成
  const defaultPath = `/src/${id.toLowerCase()}/${id}.js`;
  
  // 統一要件オブジェクトの作成
  const requirement: any = {
    "$schema": REQUIREMENT_META_SCHEMA_PATH,
    "$metaSchema": "Requirement",
    "id": id,
    "title": args.title,
    "description": args.desc || args.title,
    "type": "requirement",
    "implementationType": args.type,
    "outputPath": {
      "default": args.path || defaultPath
    },
    "implementation": {}
  };
  
  // 実装タイプに応じた情報を設定
  switch (args.type) {
    case "function":
      requirement.implementation.function = {
        "parameters": {
          "type": "object",
          "properties": {},
          "required": []
        },
        "returnType": {
          "type": "object",
          "description": "関数の戻り値"
        },
        "async": false
      };
      break;
    case "struct":
      requirement.implementation.struct = {
        "properties": {},
        "methods": {}
      };
      break;
    case "string":
      requirement.implementation.string = {
        "validation": {}
      };
      break;
    case "enum":
      requirement.implementation.enum = {
        "values": []
      };
      break;
  }
  
  // 依存要件の設定
  if (args.deps) {
    requirement.dependencies = args.deps.split(",").map((dep: string) => dep.trim());
  } else {
    requirement.dependencies = [];
  }
  
  // メタデータの追加
  const now = new Date().toISOString();
  requirement.status = "draft";
  requirement.priority = "medium";
  requirement.createdAt = now;
  requirement.updatedAt = now;
  
  // 出力先ファイルパス
  const outputFilePath = join(args.outDir, `${id}.require.json`);
  
  // 既存ファイルの存在チェック
  try {
    await Deno.stat(outputFilePath);
    if (!args.force) {
      console.error(`エラー: 統一要件ファイル ${outputFilePath} は既に存在します。上書きするには --force オプションを使用してください`);
      Deno.exit(1);
    }
  } catch (error) {
    // ファイルが存在しない場合は問題なし
    if (!(error instanceof Deno.errors.NotFound)) {
      throw error;
    }
  }
  
  // 統一要件JSONの書き込み
  await Deno.writeTextFile(outputFilePath, JSON.stringify(requirement, null, 2));
  console.log(`統一要件 ${id} を ${outputFilePath} に作成しました`);
}

/**
 * 既存の要件および設定ファイルを統一要件形式に変換
 * 
 * @param requirementId 要件ID
 * @param args コマンドライン引数
 */
async function convertRequirement(requirementId: string, args: any) {
  // 要件ファイルの読み込み
  const requirementFilePath = join(args.oldReqDir, `${requirementId}.json`);
  let requirement;
  
  try {
    const content = await Deno.readTextFile(requirementFilePath);
    requirement = JSON.parse(content);
  } catch (error) {
    console.error(`要件ファイル ${requirementFilePath} の読み込みに失敗しました: ${error.message}`);
    console.log("要件ファイルが存在しない場合は、設定ファイルのみから変換を試みます");
    requirement = null;
  }
  
  // 実装タイプの取得 (要件ファイルがない場合は設定ファイルから推測)
  let implementationType = requirement?.outputType;
  
  // 設定ファイルのパターンを試す
  const configPatterns = [
    `${requirementId}.Function.config.json`,
    `${requirementId}.Struct.config.json`,
    `${requirementId}.String.config.json`,
    `${requirementId}.Enum.config.json`
  ];
  
  let configFile = null;
  let configFilePath = "";
  
  for (const pattern of configPatterns) {
    const path = join(args.oldConfigDir, pattern);
    try {
      const content = await Deno.readTextFile(path);
      configFile = JSON.parse(content);
      configFilePath = path;
      
      // 要件ファイルがない場合は設定ファイルからタイプを取得
      if (!implementationType) {
        const match = pattern.match(/\.([A-Za-z]+)\.config\.json$/);
        if (match) {
          implementationType = match[1].toLowerCase();
        }
      }
      
      break;
    } catch (error) {
      // ファイルが見つからない場合は次のパターンを試す
      continue;
    }
  }
  
  if (!configFile && !requirement) {
    console.error(`エラー: ${requirementId} に対応する要件ファイルも設定ファイルも見つかりませんでした`);
    Deno.exit(1);
  }
  
  // 統一要件オブジェクトの作成
  const unifiedRequirement: any = {
    "$schema": REQUIREMENT_META_SCHEMA_PATH,
    "$metaSchema": "Requirement",
    "id": requirementId,
    "title": requirement?.title || configFile?.title || requirementId,
    "description": requirement?.description || configFile?.description || "",
    "type": "requirement",
    "implementationType": implementationType,
    "implementation": {}
  };
  
  // 要件情報のコピー
  if (requirement) {
    // 出力パス
    unifiedRequirement.outputPath = requirement.outputPath;
    
    // メタデータ
    unifiedRequirement.status = requirement.status || "draft";
    unifiedRequirement.priority = requirement.priority || "medium";
    unifiedRequirement.createdAt = requirement.createdAt || new Date().toISOString();
    unifiedRequirement.updatedAt = new Date().toISOString();
    
    // 依存関係
    unifiedRequirement.dependencies = requirement.dependencies || [];
    
    // タグ
    if (requirement.tags) {
      unifiedRequirement.tags = requirement.tags;
    }
  } else {
    // 要件情報がない場合のデフォルト
    unifiedRequirement.outputPath = {
      "default": `/src/${requirementId.toLowerCase()}/${requirementId}.js`
    };
    unifiedRequirement.status = "draft";
    unifiedRequirement.priority = "medium";
    const now = new Date().toISOString();
    unifiedRequirement.createdAt = now;
    unifiedRequirement.updatedAt = now;
    unifiedRequirement.dependencies = [];
  }
  
  // 設定ファイル情報のコピー
  if (configFile) {
    // 実装タイプに応じた情報をコピー
    switch (implementationType) {
      case "function":
        unifiedRequirement.implementation.function = {
          parameters: configFile.parameters,
          returnType: configFile.returnType,
          async: configFile.async || false
        };
        
        // オプションフィールド
        if (configFile.exceptions) {
          unifiedRequirement.implementation.function.exceptions = configFile.exceptions;
        }
        
        if (configFile.sideEffects !== undefined) {
          unifiedRequirement.implementation.function.sideEffects = configFile.sideEffects;
        }
        break;
        
      case "struct":
        unifiedRequirement.implementation.struct = {
          properties: {}
        };
        
        // プロパティのコピー
        if (configFile.properties) {
          unifiedRequirement.implementation.struct.properties = configFile.properties;
        }
        
        // メソッドの抽出
        if (configFile.properties) {
          const methods: Record<string, any> = {};
          
          for (const [key, value] of Object.entries(configFile.properties)) {
            const prop = value as any;
            if (prop.type === "object" && prop.properties && 
                (prop.properties.parameters || prop.properties.returnType)) {
              // メソッドとして扱う
              methods[key] = {
                description: prop.description || "",
                parameters: prop.properties.parameters,
                returnType: prop.properties.returnType
              };
              
              // プロパティからは削除
              delete unifiedRequirement.implementation.struct.properties[key];
            }
          }
          
          if (Object.keys(methods).length > 0) {
            unifiedRequirement.implementation.struct.methods = methods;
          }
        }
        
        // required フィールド
        if (configFile.required) {
          unifiedRequirement.implementation.struct.required = configFile.required;
        }
        break;
        
      case "string":
        unifiedRequirement.implementation.string = {
          validation: {}
        };
        
        // バリデーション情報のコピー
        if (configFile.minLength !== undefined) {
          unifiedRequirement.implementation.string.validation.minLength = configFile.minLength;
        }
        
        if (configFile.maxLength !== undefined) {
          unifiedRequirement.implementation.string.validation.maxLength = configFile.maxLength;
        }
        
        if (configFile.pattern) {
          unifiedRequirement.implementation.string.validation.pattern = configFile.pattern;
        }
        
        if (configFile.format) {
          unifiedRequirement.implementation.string.validation.format = configFile.format;
        }
        break;
        
      case "enum":
        unifiedRequirement.implementation.enum = {
          values: []
        };
        
        // 列挙値のコピー
        if (configFile.enum && Array.isArray(configFile.enum)) {
          unifiedRequirement.implementation.enum.values = configFile.enum.map((val: any) => {
            if (typeof val === "object") {
              return val;
            } else {
              return {
                name: val.toString(),
                value: val
              };
            }
          });
        }
        break;
    }
    
    // 例があれば追加
    if (configFile.examples) {
      unifiedRequirement.examples = configFile.examples;
    }
    
    // タグがある場合は追加/マージ
    if (configFile.tags) {
      if (unifiedRequirement.tags) {
        // タグをマージ(重複を除く)
        const allTags = new Set([...unifiedRequirement.tags, ...configFile.tags]);
        unifiedRequirement.tags = Array.from(allTags);
      } else {
        unifiedRequirement.tags = configFile.tags;
      }
    }
    
    // 非推奨情報
    if (configFile.deprecated !== undefined) {
      unifiedRequirement.deprecated = configFile.deprecated;
      
      if (configFile.deprecationMessage) {
        unifiedRequirement.deprecationMessage = configFile.deprecationMessage;
      }
    }
  }
  
  // 出力先ファイルパス
  const outputFilePath = join(args.outDir, `${requirementId}.require.json`);
  
  // 既存ファイルの存在チェック
  try {
    await Deno.stat(outputFilePath);
    if (!args.force) {
      console.error(`エラー: 統一要件ファイル ${outputFilePath} は既に存在します。上書きするには --force オプションを使用してください`);
      Deno.exit(1);
    }
  } catch (error) {
    // ファイルが存在しない場合は問題なし
    if (!(error instanceof Deno.errors.NotFound)) {
      throw error;
    }
  }
  
  // 統一要件JSONの書き込み
  await Deno.writeTextFile(outputFilePath, JSON.stringify(unifiedRequirement, null, 2));
  console.log(`要件 ${requirementId} を統一要件形式に変換し、${outputFilePath} に保存しました`);
}

/**
 * 統一要件の一覧を表示
 * 
 * @param dirPath 統一要件ファイルが格納されているディレクトリパス
 */
async function listRequirements(dirPath: string) {
  try {
    // ディレクトリ内のファイル一覧を取得
    const entries = Deno.readDirSync(dirPath);
    
    // 統一要件の配列
    const requirements: any[] = [];
    
    // JSONファイルをフィルタリングして読み込む
    for (const entry of entries) {
      if (entry.isFile && entry.name.endsWith('.require.json')) {
        try {
          const filePath = join(dirPath, entry.name);
          const content = await Deno.readTextFile(filePath);
          const requirement = JSON.parse(content);
          
          if (requirement.$metaSchema === "Requirement") {
            requirements.push(requirement);
          }
        } catch (error) {
          console.error(`ファイル ${entry.name} の読み込み/解析に失敗しました: ${error.message}`);
        }
      }
    }
    
    if (requirements.length === 0) {
      console.log(`ディレクトリ ${dirPath} に統一要件が見つかりませんでした`);
      return;
    }
    
    // IDでソート
    requirements.sort((a, b) => a.id.localeCompare(b.id));
    
    // 表示
    console.log(`\n統一要件一覧 (${requirements.length}件):\n`);
    
    requirements.forEach(req => {
      console.log(`ID: ${req.id}`);
      console.log(`タイトル: ${req.title}`);
      console.log(`説明: ${req.description}`);
      console.log(`実装タイプ: ${req.implementationType}`);
      console.log(`状態: ${req.status || '未設定'}`);
      
      if (req.dependencies && req.dependencies.length > 0) {
        console.log(`依存要件: ${req.dependencies.join(', ')}`);
      }
      
      console.log(`作成日時: ${req.createdAt || '未設定'}`);
      console.log(`更新日時: ${req.updatedAt || '未設定'}`);
      console.log('-'.repeat(50));
    });
  } catch (error) {
    console.error(`ディレクトリ ${dirPath} の読み込みに失敗しました: ${error.message}`);
    Deno.exit(1);
  }
}

/**
 * 統一要件を検証
 * 
 * @param requirementId 要件ID
 * @param args コマンドライン引数
 */
async function validateRequirement(requirementId: string, args: any) {
  // 統一要件メタスキーマの読み込み
  const metaSchema = await loadRequirementMetaSchema(args.metaDir);
  
  // 統一要件ファイルの読み込み
  const requirementFilePath = join(args.outDir, `${requirementId}.require.json`);
  let requirement;
  
  try {
    const content = await Deno.readTextFile(requirementFilePath);
    requirement = JSON.parse(content);
  } catch (error) {
    console.error(`統一要件ファイル ${requirementFilePath} の読み込みに失敗しました: ${error.message}`);
    Deno.exit(1);
  }
  
  // 要件の基本検証
  const validationErrors: string[] = [];
  
  // 必須フィールドのチェック
  for (const field of ["id", "title", "description", "type", "implementationType"]) {
    if (!requirement[field]) {
      validationErrors.push(`必須フィールド '${field}' がありません`);
    }
  }
  
  // IDフォーマットのチェック
  if (requirement.id && typeof requirement.id === 'string') {
    if (!/^[a-zA-Z0-9-_]+$/.test(requirement.id)) {
      validationErrors.push("IDには英数字、ハイフン、アンダースコアのみ使用できます");
    }
  }
  
  // 実装タイプのチェック
  const validTypes = ["function", "struct", "string", "enum"];
  if (requirement.implementationType && !validTypes.includes(requirement.implementationType)) {
    validationErrors.push(`実装タイプは ${validTypes.join(", ")} のいずれかである必要があります`);
  }
  
  // 出力パスのチェック
  if (!requirement.outputPath || !requirement.outputPath.default) {
    validationErrors.push("`outputPath.default` が必要です");
  }
  
  // 実装情報のチェック
  if (requirement.implementationType === "function" && 
      (!requirement.implementation || !requirement.implementation.function)) {
    validationErrors.push("関数型の場合は実装情報に `function` プロパティが必要です");
  } else if (requirement.implementationType === "struct" && 
           (!requirement.implementation || !requirement.implementation.struct)) {
    validationErrors.push("構造体型の場合は実装情報に `struct` プロパティが必要です");
  } else if (requirement.implementationType === "string" && 
           (!requirement.implementation || !requirement.implementation.string)) {
    validationErrors.push("文字列型の場合は実装情報に `string` プロパティが必要です");
  } else if (requirement.implementationType === "enum" && 
           (!requirement.implementation || !requirement.implementation.enum)) {
    validationErrors.push("列挙型の場合は実装情報に `enum` プロパティが必要です");
  }
  
  // 依存要件のチェック
  if (requirement.dependencies && !Array.isArray(requirement.dependencies)) {
    validationErrors.push("`dependencies` は配列である必要があります");
  }
  
  // 結果の表示
  if (validationErrors.length > 0) {
    console.error(`統一要件 ${requirementId} に以下の問題が見つかりました:`);
    validationErrors.forEach(error => console.error(` - ${error}`));
    Deno.exit(1);
  } else {
    console.log(`統一要件 ${requirementId} は有効です`);  
    
    // 詳細情報の表示
    console.log('\n統一要件の内容:');
    console.log(`ID: ${requirement.id}`);
    console.log(`タイトル: ${requirement.title}`);
    console.log(`説明: ${requirement.description}`);
    console.log(`実装タイプ: ${requirement.implementationType}`);
    console.log(`状態: ${requirement.status || '未設定'}`);
    
    if (requirement.dependencies && requirement.dependencies.length > 0) {
      console.log(`依存要件: ${requirement.dependencies.join(', ')}`);
    }
    
    console.log(`出力パス: ${requirement.outputPath.default}`);
  }
}
