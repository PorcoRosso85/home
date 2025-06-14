#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run

/**
 * 統合要件から型スキーマを生成するスクリプト
 */
async function main() {
  console.log("=== 統合要件から型スキーマ生成開始 ===");

  try {
    // 統合要件ファイルの一覧を取得
    const reqFiles = await getUnifiedRequirementFiles();
    
    if (reqFiles.length === 0) {
      console.log("統合要件ファイルが見つかりませんでした");
      return;
    }
    
    // 各統合要件からスキーマを生成
    for (const reqFile of reqFiles) {
      await generateSchemaFromUnifiedRequirement(reqFile);
    }

    console.log("\n=== 生成完了 ===");
  } catch (error) {
    console.error("エラーが発生しました:", error.message);
    Deno.exit(1);
  }
}

/**
 * 統合要件ファイルの一覧を取得する
 */
async function getUnifiedRequirementFiles(): Promise<string[]> {
  const reqFiles: string[] = [];
  
  try {
    for await (const entry of Deno.readDir("./data/config")) {
      if (entry.isFile && entry.name.endsWith(".req.config.json")) {
        reqFiles.push(entry.name);
      }
    }
  } catch (error) {
    console.error("ディレクトリの読み込みに失敗しました:", error.message);
  }
  
  return reqFiles;
}

/**
 * 統合要件からスキーマを生成する
 * 
 * @param reqFileName 統合要件ファイル名
 */
async function generateSchemaFromUnifiedRequirement(reqFileName: string): Promise<void> {
  try {
    // ファイル名から要件IDを抽出
    const match = reqFileName.match(/^(.+)\.req\.config\.json$/);
    if (!match) {
      throw new Error(`ファイル名 ${reqFileName} が正しい形式ではありません`);
    }
    
    const reqId = match[1];
    console.log(`\n=== ${reqId}の生成 ===`);
    
    // 統合要件ファイルを読み込む
    const reqFilePath = `./data/config/${reqFileName}`;
    const reqContent = await Deno.readTextFile(reqFilePath);
    const reqData = JSON.parse(reqContent);
    
    // 実装タイプを取得
    const implType = reqData.implementationType;
    if (!implType) {
      throw new Error(`要件 ${reqId} に実装タイプが指定されていません`);
    }
    
    // 実装タイプを大文字で始める（functionをFunctionにするなど）
    const metaSchemaType = implType.charAt(0).toUpperCase() + implType.slice(1);
    
    // 出力パスを作成
    const outputPath = `./data/generated/${reqId}.${metaSchemaType}.schema.json`;
    
    // スキーマを生成
    console.log(`統合要件 ${reqFilePath} からスキーマを生成中...`);
    await generateUnifiedSchema(reqId, reqFilePath, metaSchemaType, outputPath);
    
    // 成功メッセージ
    console.log(`スキーマを ${outputPath} に生成しました`);
    
    // 生成されたスキーマの内容を確認
    try {
      const schema = await Deno.readTextFile(outputPath);
      const schemaObj = JSON.parse(schema);
      console.log(`- タイトル: ${schemaObj.title || "未設定"}`);
      console.log(`- タイプ: ${schemaObj.type || "未設定"}`);
      console.log(`- プロパティ数: ${Object.keys(schemaObj.properties || {}).length}`);
    } catch (error) {
      console.error("生成されたスキーマの確認に失敗しました:", error.message);
    }
  } catch (error) {
    console.error(`${reqFileName} からのスキーマ生成に失敗しました:`, error.message);
  }
}

/**
 * 統合要件からスキーマを生成する（内部処理）
 * 
 * @param reqId 要件ID
 * @param reqFilePath 統合要件ファイルパス
 * @param metaSchemaType メタスキーマタイプ
 * @param outputPath 出力先パス
 */
async function generateUnifiedSchema(
  reqId: string,
  reqFilePath: string,
  metaSchemaType: string,
  outputPath: string
): Promise<void> {
  try {
    // 統合要件ファイルを読み込む
    const reqContent = await Deno.readTextFile(reqFilePath);
    const reqData = JSON.parse(reqContent);
    
    // 実装情報を取得
    const implInfo = reqData.implementation[reqData.implementationType.toLowerCase()];
    if (!implInfo) {
      throw new Error(`要件 ${reqId} に ${reqData.implementationType} 実装情報がありません`);
    }
    
    // 必要なデータを取得して新しいスキーマを作成
    const schemaData: any = {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "$metaSchema": metaSchemaType,
      "title": reqData.title,
      "description": reqData.description
    };
    
    // 実装タイプに応じた処理
    switch (reqData.implementationType.toLowerCase()) {
      case "function":
        schemaData.type = "function";
        if (implInfo.parameters) schemaData.parameters = implInfo.parameters;
        if (implInfo.returnType) schemaData.returnType = implInfo.returnType;
        if (implInfo.async !== undefined) schemaData.async = implInfo.async;
        if (implInfo.exceptions) schemaData.exceptions = implInfo.exceptions;
        if (implInfo.sideEffects !== undefined) schemaData.sideEffects = implInfo.sideEffects;
        break;
        
      case "struct":
        schemaData.type = "object";
        if (implInfo.properties) schemaData.properties = implInfo.properties;
        if (implInfo.required) schemaData.required = implInfo.required;
        if (implInfo.methods) {
          // メソッドをプロパティに変換
          if (!schemaData.properties) schemaData.properties = {};
          
          for (const [methodName, methodInfo] of Object.entries<any>(implInfo.methods)) {
            schemaData.properties[methodName] = {
              type: "object",
              description: methodInfo.description || `${methodName} メソッド`,
              properties: {}
            };
            
            if (methodInfo.parameters) {
              schemaData.properties[methodName].properties.parameters = methodInfo.parameters;
            }
            
            if (methodInfo.returnType) {
              schemaData.properties[methodName].properties.returnType = methodInfo.returnType;
            }
          }
        }
        break;
        
      case "string":
        schemaData.type = "string";
        if (implInfo.validation) {
          Object.assign(schemaData, implInfo.validation);
        }
        break;
        
      case "enum":
        schemaData.type = "string";
        if (implInfo.values && Array.isArray(implInfo.values)) {
          schemaData.enum = implInfo.values.map((v: any) => v.name || v);
          
          // 列挙値の説明を含む場合
          const enumDescriptions = implInfo.values
            .filter((v: any) => v.description)
            .map((v: any) => `${v.name}: ${v.description}`);
            
          if (enumDescriptions.length > 0) {
            const enumDesc = enumDescriptions.join("\n");
            schemaData.description = schemaData.description 
              ? `${schemaData.description}\n\n列挙値:\n${enumDesc}` 
              : `列挙値:\n${enumDesc}`;
          }
        }
        break;
        
      default:
        throw new Error(`未サポートの実装タイプ: ${reqData.implementationType}`);
    }
    
    // 詳細情報をスキーマに追加
    if (reqData.tags) schemaData.tags = reqData.tags;
    if (reqData.deprecated !== undefined) schemaData.deprecated = reqData.deprecated;
    if (reqData.examples) schemaData.examples = reqData.examples;
    
    // スキーマをJSON文字列化
    const schemaContent = JSON.stringify(schemaData, null, 2);
    
    // ファイルに書き込む
    await Deno.writeTextFile(outputPath, schemaContent);
    
  } catch (error) {
    throw new Error(`スキーマの生成に失敗しました: ${error.message}`);
  }
}

// メイン関数を実行
if (import.meta.main) {
  main().catch(err => {
    console.error("スクリプト実行中にエラーが発生しました:", err.message);
    Deno.exit(1);
  });
}
