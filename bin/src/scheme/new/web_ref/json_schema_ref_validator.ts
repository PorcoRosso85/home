#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run

/**
 * JSON Schema $ref検証機能
 * 
 * このモジュールはJSON Schemaにおける$ref参照の検証を行います。
 * 主な機能は以下の通りです：
 * 
 * 1. $refの構文的な妥当性検証
 * 2. 参照先のスキーマファイルまたは定義が存在するかの検証
 * 3. 循環参照の検出
 * 
 * 大規模なJSON Schemaを扱う際に発生しがちな参照エラーを早期に発見し、
 * より堅牢なスキーマ管理を実現することを目的としています。
 */

interface RefValidationError {
  path: string;
  message: string;
  refValue: string;
}

interface ValidationOptions {
  baseDir?: string;
  resolveRemote?: boolean;
  maxDepth?: number;
}

/**
 * JSON Schema内の$ref参照を検証するクラス
 */
export class JsonSchemaRefValidator {
  private readonly options: Required<ValidationOptions>;
  private readonly visitedRefs: Set<string> = new Set();
  private readonly errors: RefValidationError[] = [];
  private readonly resolvedSchemas: Map<string, any> = new Map();

  /**
   * バリデータのコンストラクタ
   * @param options 検証オプション
   */
  constructor(options: ValidationOptions = {}) {
    this.options = {
      baseDir: options.baseDir ?? Deno.cwd(),
      resolveRemote: options.resolveRemote ?? false,
      maxDepth: options.maxDepth ?? 10,
    };
  }

  /**
   * JSONスキーマ内の$ref参照を検証する
   * @param schema 検証対象のJSONスキーマ（オブジェクトまたはファイルパス）
   * @returns 検証エラーの配列
   */
  async validate(schema: any | string): Promise<RefValidationError[]> {
    this.errors.length = 0;
    this.visitedRefs.clear();
    this.resolvedSchemas.clear();

    const schemaObj = typeof schema === 'string' 
      ? await this.loadSchemaFromFile(schema)
      : schema;

    if (!schemaObj) {
      this.errors.push({
        path: 'root',
        message: 'スキーマの読み込みに失敗しました',
        refValue: typeof schema === 'string' ? schema : 'inline schema',
      });
      return this.errors;
    }

    await this.validateSchema(schemaObj, 'root', 0);
    return this.errors;
  }

  /**
   * ファイルからJSONスキーマを読み込む
   * @param filePath スキーマファイルのパス
   * @returns 読み込まれたスキーマオブジェクト
   */
  private async loadSchemaFromFile(filePath: string): Promise<any> {
    try {
      const path = filePath.startsWith('/')
        ? filePath
        : `${this.options.baseDir}/${filePath}`;

      const fileContent = await Deno.readTextFile(path);
      return JSON.parse(fileContent);
    } catch (error) {
      this.errors.push({
        path: 'file',
        message: `ファイル読み込みエラー: ${error instanceof Error ? error.message : String(error)}`,
        refValue: filePath,
      });
      return null;
    }
  }

  /**
   * JSONスキーマオブジェクトを再帰的に検証
   * @param schema 検証対象のスキーマオブジェクト
   * @param path 現在の検証パス
   * @param depth 現在の再帰の深さ
   */
  private async validateSchema(schema: any, path: string, depth: number): Promise<void> {
    // 最大深度チェック
    if (depth > this.options.maxDepth) {
      this.errors.push({
        path,
        message: '最大参照深度を超えました。循環参照の可能性があります',
        refValue: path,
      });
      return;
    }

    // nullまたは非オブジェクトのスキーマはスキップ
    if (!schema || typeof schema !== 'object') {
      return;
    }

    // 配列の場合は各要素を検証
    if (Array.isArray(schema)) {
      for (let i = 0; i < schema.length; i++) {
        await this.validateSchema(schema[i], `${path}[${i}]`, depth);
      }
      return;
    }

    // $refの検証
    if (schema.$ref && typeof schema.$ref === 'string') {
      // 無効な$ref構文のチェックをインラインで行う
      if (!this.isValidRefSyntax(schema.$ref)) {
        this.errors.push({
          path,
          message: '無効な$ref構文です',
          refValue: schema.$ref,
        });
      }
      await this.validateRef(schema.$ref, path, depth);
    }

    // スキーマ内の他のプロパティを再帰的に検証
    for (const [key, value] of Object.entries(schema)) {
      if (key !== '$ref' && typeof value === 'object' && value !== null) {
        await this.validateSchema(value, `${path}.${key}`, depth);
      }
    }
  }

  /**
   * $ref参照を検証する
   * @param refValue $refの値
   * @param path 現在の検証パス
   * @param depth 現在の再帰の深さ
   */
  private async validateRef(refValue: string, path: string, depth: number): Promise<void> {
    // 循環参照チェック
    if (this.visitedRefs.has(refValue)) {
      this.errors.push({
        path,
        message: '循環参照が検出されました',
        refValue,
      });
      return;
    }

    this.visitedRefs.add(refValue);

    // $refの構文チェック
    if (!this.isValidRefSyntax(refValue)) {
      this.errors.push({
        path,
        message: '無効な$ref構文です',
        refValue,
      });
      return;
    }

    // リモート参照と非リモート参照で分岐
    if (refValue.startsWith('http://') || refValue.startsWith('https://')) {
      if (!this.options.resolveRemote) {
        this.errors.push({
          path,
          message: 'リモート参照の解決は無効化されています',
          refValue,
        });
        return;
      }
      await this.validateRemoteRef(refValue, path, depth);
    } else {
      await this.validateLocalRef(refValue, path, depth);
    }

    this.visitedRefs.delete(refValue);
  }

  /**
   * $refの構文が有効かチェック
   * @param refValue $refの値
   * @returns 構文が有効な場合はtrue
   */
  private isValidRefSyntax(refValue: string): boolean {
    // URIまたはURIフラグメント形式の確認
    if (refValue.startsWith('#/')) {
      // JSONポインタのフォーマット確認 (#/path/to/definition)
      return /^#(\/[^/]+)*$/.test(refValue);
    } else if (refValue.startsWith('http://') || refValue.startsWith('https://')) {
      // URLの基本的な妥当性確認
      try {
        new URL(refValue);
        return true;
      } catch {
        return false;
      }
    } else {
      // ファイル参照形式の確認 (file.json#/path または file.json)
      return /^[^#]+(?:#(\/[^/]+)*)?$/.test(refValue);
    }
  }

  /**
   * ローカル$ref参照を検証
   * @param refValue $refの値
   * @param path 現在の検証パス
   * @param depth 現在の再帰の深さ
   */
  private async validateLocalRef(refValue: string, path: string, depth: number): Promise<void> {
    // 内部参照 (#/definitions/...)
    if (refValue.startsWith('#/')) {
      // 実装しない（メインスキーマにアクセスする方法に依存するため）
      return;
    }

    // ファイル参照 (file.json または file.json#/path)
    const [filePath, fragment] = refValue.split('#');
    
    // すでに解決済みのスキーマがあれば再利用
    if (!this.resolvedSchemas.has(filePath)) {
      const referencedSchema = await this.loadSchemaFromFile(filePath);
      if (referencedSchema) {
        this.resolvedSchemas.set(filePath, referencedSchema);
      } else {
        this.errors.push({
          path,
          message: '参照先のスキーマファイルが見つかりません',
          refValue,
        });
        return;
      }
    }

    const schema = this.resolvedSchemas.get(filePath);
    
    // フラグメントが指定されている場合は参照先の存在を確認
    if (fragment && fragment.startsWith('/')) {
      const pathParts = fragment.substring(1).split('/');
      let current = schema;
      
      for (const part of pathParts) {
        const decodedPart = decodeURIComponent(part);
        if (!current || typeof current !== 'object' || !(decodedPart in current)) {
          this.errors.push({
            path,
            message: `参照先の定義 "${fragment}" が見つかりません`,
            refValue,
          });
          return;
        }
        current = current[decodedPart];
      }
    }
    
    // 参照先のスキーマで再帰的に$refを検証
    if (fragment && fragment.startsWith('/')) {
      const pathParts = fragment.substring(1).split('/');
      let current = schema;
      
      for (const part of pathParts) {
        const decodedPart = decodeURIComponent(part);
        if (!current || !current[decodedPart]) {
          return;
        }
        current = current[decodedPart];
      }
      
      if (current) {
        await this.validateSchema(current, `${path}->$ref(${refValue})`, depth + 1);
      }
    } else {
      await this.validateSchema(schema, `${path}->$ref(${refValue})`, depth + 1);
    }
  }

  /**
   * リモート$ref参照を検証
   * @param refValue $refの値
   * @param path 現在の検証パス
   * @param depth 現在の再帰の深さ
   */
  private async validateRemoteRef(refValue: string, path: string, depth: number): Promise<void> {
    // リモート参照の検証はオプション機能
    // 実際のHTTPリクエストは行わず、構文チェックのみ
    this.errors.push({
      path,
      message: 'リモート参照の実際の検証は実装されていません',
      refValue,
    });
  }
}

// このファイルが直接実行された場合の処理
if (import.meta.main) {
  if (Deno.args.length === 0) {
    console.log("使用方法: json_schema_ref_validator.ts <schema_file_path> [ベースディレクトリ]");
    Deno.exit(1);
  }
  
  const schemaPath = Deno.args[0];
  // 基準ディレクトリが指定されていれば使用、そうでなければスキーマファイルの親ディレクトリを使用
  const baseDir = Deno.args[1] || new URL('./', new URL(schemaPath, `file://${Deno.cwd()}/`)).pathname;
  
  const validator = new JsonSchemaRefValidator({ baseDir });
  console.log(`スキーマファイル ${schemaPath} の$ref検証を開始します...`);
  console.log(`基準ディレクトリ: ${baseDir}`);
  
  validator.validate(schemaPath).then(errors => {
    if (errors.length === 0) {
      console.log("✅ 検証成功: エラーは見つかりませんでした");
      Deno.exit(0);
    } else {
      console.log(`❌ 検証失敗: ${errors.length}件のエラーが見つかりました`);
      errors.forEach((error, index) => {
        console.log(`\nエラー #${index + 1}:`);
        console.log(`パス: ${error.path}`);
        console.log(`メッセージ: ${error.message}`);
        console.log(`参照値: ${error.refValue}`);
      });
      Deno.exit(1);
    }
  }).catch(error => {
    console.error("検証中にエラーが発生しました:", error);
    Deno.exit(1);
  });
}
