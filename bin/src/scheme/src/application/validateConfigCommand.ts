#!/usr/bin/env -S deno run --allow-read --allow-write

import { Command } from './command.ts';

/**
 * 設定ファイルを検証するコマンド
 * 文字列型の設定ファイルを検証し、有効であればスキーマを生成する
 */
export class ValidateConfigCommand implements Command {
  /**
   * コマンドを実行する
   * 
   * @param args コマンドライン引数（設定ファイルのパス）
   */
  async execute(args: string[]): Promise<void> {
    try {
      // 1. メタスキーマの読み込み
      console.log("1. メタスキーマを読み込んでいます...");
      const metaSchemaText = await Deno.readTextFile("./string-type-meta.json");
      const metaSchema = JSON.parse(metaSchemaText);
      
      // 2. 設定ファイルの読み込み
      console.log("\n2. 設定ファイルを読み込んでいます...");
      const configPath = args[0] || "./invalid-userId-config.json";
      let config;
      
      try {
        const configText = await Deno.readTextFile(configPath);
        config = JSON.parse(configText);
        console.log(`設定ファイル '${configPath}' を読み込みました`);
      } catch (error) {
        if (error instanceof Deno.errors.NotFound) {
          console.error(`エラー: ファイル '${configPath}' が見つかりません`);
          Deno.exit(1);
        } else if (error.message.includes('JSON')) {
          console.error(`エラー: ファイル '${configPath}' は有効なJSONではありません`);
          console.error(error.message);
          Deno.exit(1);
        } else {
          throw error;
        }
      }
      
      // 3. 設定ファイルを検証
      console.log("\n3. 設定ファイルを検証しています...");
      const validationResult = this.validateStringTypeConfig(config);
      
      // 4. 検証結果を表示
      console.log("\n4. 検証結果:");
      if (validationResult.valid) {
        console.log("✅ 設定ファイルは有効です");
        
        // 5. 有効な設定からスキーマを生成
        console.log("\n5. スキーマを生成しています...");
        const schema = this.generateStringTypeSchema(config);
        console.log("生成されたスキーマ:");
        console.log(JSON.stringify(schema, null, 2));
        
      } else {
        console.log("❌ 設定ファイルには以下の問題があります:");
        validationResult.errors.forEach(error => {
          console.log(`  - ${error}`);
        });
        
        console.log("\n問題のある設定:");
        console.log(JSON.stringify(config, null, 2));
      }
      
    } catch (error) {
      console.error(`処理中にエラーが発生しました: ${error.message}`);
      Deno.exit(1);
    }
  }

  /**
   * 文字列型の設定を検証する関数
   * 
   * @param config 検証する設定オブジェクト
   * @returns 検証結果（有効かどうかとエラーメッセージの配列）
   */
  private validateStringTypeConfig(config: any): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // title は必須
    if (!config.title) {
      errors.push("設定に必須フィールド 'title' がありません");
    } else if (typeof config.title !== 'string') {
      errors.push("'title' は文字列である必要があります");
    }
    
    // pattern が指定されている場合、有効な正規表現か検証
    if (config.pattern !== undefined) {
      if (typeof config.pattern !== 'string') {
        errors.push("'pattern' は文字列である必要があります");
      } else {
        try {
          new RegExp(config.pattern);
        } catch (e) {
          errors.push(`'pattern' は有効な正規表現である必要があります: ${e.message}`);
        }
      }
    }
    
    // minLength が指定されている場合、数値か検証
    if (config.minLength !== undefined) {
      if (typeof config.minLength !== 'number' || config.minLength < 0 || !Number.isInteger(config.minLength)) {
        errors.push("'minLength' は0以上の整数である必要があります");
      }
    }
    
    // maxLength が指定されている場合、数値か検証
    if (config.maxLength !== undefined) {
      if (typeof config.maxLength !== 'number' || config.maxLength < 0 || !Number.isInteger(config.maxLength)) {
        errors.push("'maxLength' は0以上の整数である必要があります");
      }
    }
    
    // minLength と maxLength の整合性を検証
    if (config.minLength !== undefined && config.maxLength !== undefined) {
      if (typeof config.minLength === 'number' && typeof config.maxLength === 'number' && config.minLength > config.maxLength) {
        errors.push("'minLength' は 'maxLength' 以下である必要があります");
      }
    }
    
    // format が指定されている場合、有効な値か検証
    if (config.format !== undefined) {
      const validFormats = ["email", "hostname", "ipv4", "ipv6", "uri", "date", "date-time", "uuid"];
      if (!validFormats.includes(config.format)) {
        errors.push(`'format' は次のいずれかである必要があります: ${validFormats.join(', ')}`);
      }
    }
    
    // examples が指定されている場合、配列か検証
    if (config.examples !== undefined) {
      if (!Array.isArray(config.examples)) {
        errors.push("'examples' は配列である必要があります");
      } else {
        // 各例が文字列であることを検証
        for (let i = 0; i < config.examples.length; i++) {
          if (typeof config.examples[i] !== 'string') {
            errors.push(`'examples[${i}]' は文字列である必要があります`);
          }
        }
      }
    }
    
    // enum が指定されている場合、配列か検証
    if (config.enum !== undefined) {
      if (!Array.isArray(config.enum)) {
        errors.push("'enum' は配列である必要があります");
      } else {
        // 各値が文字列であることを検証
        for (let i = 0; i < config.enum.length; i++) {
          if (typeof config.enum[i] !== 'string') {
            errors.push(`'enum[${i}]' は文字列である必要があります`);
          }
        }
      }
    }
    
    // default が指定されている場合、文字列か検証
    if (config.default !== undefined && typeof config.default !== 'string') {
      errors.push("'default' は文字列である必要があります");
    }
    
    // 未知のプロパティがないか検証
    const knownProps = ['title', 'description', 'pattern', 'minLength', 'maxLength', 
                         'format', 'examples', 'enum', 'default'];
    const unknownProps = Object.keys(config).filter(key => !knownProps.includes(key));
    
    if (unknownProps.length > 0) {
      errors.push(`未知のプロパティが含まれています: ${unknownProps.join(', ')}`);
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * 文字列型スキーマの生成関数
   * 
   * @param config 設定オブジェクト
   * @returns 生成されたJSONスキーマオブジェクト
   */
  private generateStringTypeSchema(config: any): any {
    const baseSchema = {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "$metaSchema": "StringTypeMetaSchema",
      "type": "string"
    };
    
    // 設定からプロパティをコピー
    const schema = { ...baseSchema };
    
    // 各プロパティを設定
    Object.keys(config).forEach(key => {
      schema[key] = config[key];
    });
    
    return schema;
  }
}

// スクリプトを実行
if (import.meta.main) {
  const command = new ValidateConfigCommand();
  command.execute(Deno.args);
}
