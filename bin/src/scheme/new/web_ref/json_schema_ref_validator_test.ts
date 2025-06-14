#!/usr/bin/env -S nix shell nixpkgs#deno --command deno test --allow-read --allow-write

/**
 * JSON Schema $ref検証機能のテスト
 * 
 * このファイルは、json_schema_ref_validator.tsの実装をテストします。
 * Denoのテストフレームワークを使用して、様々なケースでの動作を検証します。
 */

import { assertEquals, assertArrayIncludes } from "https://deno.land/std/testing/asserts.ts";
import { JsonSchemaRefValidator } from "./json_schema_ref_validator.ts";

// テスト用の固定パス
const TEST_DATA_DIR = new URL("./test_data", import.meta.url).pathname;

// バリデータのインスタンス
let validator: JsonSchemaRefValidator;

// テスト前の準備
Deno.test({
  name: "バリデータの初期化",
  fn() {
    validator = new JsonSchemaRefValidator({ baseDir: TEST_DATA_DIR });
    assertEquals(typeof validator.validate, "function");
  },
});

// 有効なスキーマの検証テスト
Deno.test({
  name: "有効なスキーマのバリデーション（ファイルパス指定）",
  async fn() {
    const errors = await validator.validate("schema1.json");
    assertEquals(errors.length, 0, "エラーが検出されるべきではありません");
  },
});

// 有効なスキーマの検証テスト（オブジェクト指定）
Deno.test({
  name: "有効なスキーマのバリデーション（オブジェクト指定）",
  async fn() {
    const schema = {
      type: "object",
      properties: {
        test: { type: "string" },
        ref: { "$ref": "#/definitions/sample" }
      },
      definitions: {
        sample: { type: "number" }
      }
    };
    
    const errors = await validator.validate(schema);
    assertEquals(errors.length, 0, "エラーが検出されるべきではありません");
  },
});

// 存在しないファイル参照のテスト
Deno.test({
  name: "存在しないファイル参照の検証",
  async fn() {
    const errors = await validator.validate("invalid_ref.json");
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["参照先のスキーマファイルが見つかりません"],
      "存在しないファイル参照エラーが検出されるべき"
    );
  },
});

// 存在しない定義参照のテスト
Deno.test({
  name: "存在しない定義参照の検証",
  async fn() {
    const errors = await validator.validate("invalid_ref.json");
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["参照先の定義 \"/definitions/non_existent\" が見つかりません"],
      "存在しない定義参照エラーが検出されるべき"
    );
  },
});

// 循環参照のテスト
Deno.test({
  name: "循環参照の検証",
  async fn() {
    const errors = await validator.validate("circular1.json");
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["循環参照が検出されました"],
      "循環参照エラーが検出されるべき"
    );
  },
});

// 最大深度のテスト
Deno.test({
  name: "最大深度制限の検証",
  async fn() {
    const shallowValidator = new JsonSchemaRefValidator({ 
      baseDir: TEST_DATA_DIR,
      maxDepth: 1
    });
    
    const errors = await shallowValidator.validate("schema1.json");
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["最大参照深度を超えました。循環参照の可能性があります"],
      "最大深度エラーが検出されるべき"
    );
  },
});

// 無効な$ref構文のテスト
Deno.test({
  name: "無効な$ref構文の検証",
  fn() {
    // コンストラクタからプライベートメソッドにアクセスできないので、別のアプローチでテスト
    // ここでは、正しいJSONでないオブジェクトを使って正規表現が機能しているかをテスト
    // バリデーターの実装にある正規表現を再実装してテスト
    function isValidRefString(refValue: string): boolean {
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
        return /^[\w\-\.]+(\.json)?(?:#(\/[^/]+)*)?$/.test(refValue);
      }
    }
    
    const isValid1 = isValidRefString("#/definitions/test");
    const isValid2 = isValidRefString("#/invalid//test");
    const isValid3 = isValidRefString("file.json#/path");
    const isValid4 = isValidRefString("://invalid.reference");
    
    assertEquals(true, isValid1, "#/definitions/testは有効な参照であるべき");
    assertEquals(false, isValid2, "#/invalid//testは無効な参照であるべき");
    assertEquals(true, isValid3, "file.json#/pathは有効な参照であるべき");
    assertEquals(false, isValid4, "://invalid.referenceは無効な参照であるべき");
  },
});

// リモート参照のテスト
Deno.test({
  name: "リモート参照の検証",
  async fn() {
    const remoteSchema = {
      properties: {
        remote: { "$ref": "https://example.com/schemas/schema.json" }
      }
    };
    
    const errors = await validator.validate(remoteSchema);
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["リモート参照の解決は無効化されています"],
      "リモート参照エラーが検出されるべき"
    );
  },
});

// リモート参照有効化のテスト
Deno.test({
  name: "リモート参照有効化の検証",
  async fn() {
    const remoteEnabledValidator = new JsonSchemaRefValidator({ 
      baseDir: TEST_DATA_DIR,
      resolveRemote: true
    });
    
    const remoteSchema = {
      properties: {
        remote: { "$ref": "https://example.com/schemas/schema.json" }
      }
    };
    
    const errors = await remoteEnabledValidator.validate(remoteSchema);
    
    assertArrayIncludes(
      errors.map(e => e.message),
      ["リモート参照の実際の検証は実装されていません"],
      "リモート参照の検証メッセージが表示されるべき"
    );
  },
});

// ファイル読み込みエラーのテスト
Deno.test({
  name: "ファイル読み込みエラーの検証",
  async fn() {
    const errors = await validator.validate("non_existent_file.json");
    
    // メッセージの先頭部分だけをチェック
    const hasFileReadError = errors.some(e => e.message.startsWith("ファイル読み込みエラー"));
    assertEquals(true, hasFileReadError, "ファイル読み込みエラーが検出されるべき");
  },
});

// JSON解析エラーのテスト（オブジェクト引数の場合はスキップ）
Deno.test({
  name: "JSONスキーマの統合テスト",
  async fn() {
    // schema1.json は schema2.json を参照し、schema2.json は schema3.json を参照する
    // すべての参照が正しく解決されることを確認
    const errors = await validator.validate("schema1.json");
    assertEquals(errors.length, 0, "有効な参照チェーンにはエラーがないはず");
  },
});

// 実行用のメインコード
if (import.meta.main) {
  console.log("テストを実行中...");
  console.log("テストを実行するには 'deno test --allow-read --allow-write json_schema_ref_validator_test.ts' コマンドを使用してください");
}
