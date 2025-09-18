#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --no-check

/**
 * dependencyAnalysisE2E.ts
 * 
 * 依存関係解析のE2Eテスト
 * 複雑な参照を含むテストスキーマを作成し、異なる形式での出力を検証します
 */

// 必要なモジュールのインポート
import { exists } from "https://deno.land/std/fs/mod.ts";

/**
 * テストの実行結果
 */
interface TestResult {
  passed: boolean;
  message: string;
  details?: string;
}

/**
 * メイン関数 - E2Eテストの実行
 */
async function main() {
  console.log("===== 依存関係解析 E2E テスト開始 =====");
  
  // テスト用の一時ディレクトリ作成
  const tempDir = await createTempDirectory();
  console.log(`📁 テスト用一時ディレクトリを作成しました: ${tempDir}`);
  
  try {
    // テスト用の複雑なスキーマを作成
    const schemaPath = `${tempDir}/complex-schema.json`;
    await createComplexSchema(schemaPath);
    console.log(`📄 テスト用スキーマを作成しました: ${schemaPath}`);
    
    // 各形式でのテスト実行
    const formats = ["tree", "json", "mermaid"];
    const results: Record<string, TestResult> = {};
    
    for (const format of formats) {
      console.log(`\n🧪 ${format}形式で依存関係解析をテスト中...`);
      results[format] = await testDependencyAnalysis(schemaPath, format, tempDir);
      
      if (results[format].passed) {
        console.log(`✅ ${format}形式のテストに成功しました`);
      } else {
        console.log(`❌ ${format}形式のテストに失敗しました: ${results[format].message}`);
      }
    }
    
    // 循環参照のテスト
    console.log("\n🧪 循環参照の検出をテスト中...");
    const circularSchemaPath = `${tempDir}/circular-schema.json`;
    await createCircularSchema(circularSchemaPath);
    results["circular"] = await testCircularReference(circularSchemaPath, tempDir);
    
    if (results["circular"].passed) {
      console.log("✅ 循環参照検出のテストに成功しました");
    } else {
      console.log(`❌ 循環参照検出のテストに失敗しました: ${results["circular"].message}`);
    }
    
    // 結果のサマリー表示
    console.log("\n===== テスト結果サマリー =====");
    let allPassed = true;
    
    for (const [name, result] of Object.entries(results)) {
      console.log(`${result.passed ? "✅" : "❌"} ${name}: ${result.message}`);
      if (!result.passed) allPassed = false;
    }
    
    console.log("\n===== 依存関係解析 E2E テスト終了 =====");
    console.log(allPassed ? "✅ すべてのテストに成功しました" : "❌ 一部のテストに失敗しました");
    
  } catch (error) {
    console.error("❌ テスト実行中にエラーが発生しました:", error.message);
  } finally {
    // テスト用一時ディレクトリの削除
    try {
      await Deno.remove(tempDir, { recursive: true });
      console.log(`🧹 テスト用一時ディレクトリを削除しました: ${tempDir}`);
    } catch (error) {
      console.error(`⚠️ 一時ディレクトリの削除に失敗しました: ${error.message}`);
    }
  }
}

/**
 * テスト用の一時ディレクトリを作成する
 * 
 * @returns 作成された一時ディレクトリのパス
 */
async function createTempDirectory(): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const tempDir = `./test/temp-${timestamp}`;
  
  await Deno.mkdir(tempDir, { recursive: true });
  return tempDir;
}

/**
 * 複雑な参照を持つテスト用スキーマを作成する
 * 
 * @param filePath スキーマを保存するファイルパス
 */
async function createComplexSchema(filePath: string): Promise<void> {
  const schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ComplexDependencySchema",
    "description": "複雑な依存関係を持つテスト用スキーマ",
    "type": "object",
    "properties": {
      "mainComponent": {
        "type": "object",
        "properties": {
          "processor": {
            "$ref": "#/definitions/Processor"
          },
          "storage": {
            "$ref": "#/definitions/Storage"
          },
          "interface": {
            "$ref": "#/definitions/Interface"
          }
        },
        "required": ["processor", "storage"]
      },
      "settings": {
        "type": "object",
        "properties": {
          "config": {
            "$ref": "#/definitions/Configuration"
          },
          "permissions": {
            "type": "array",
            "items": {
              "$ref": "#/definitions/Permission"
            }
          }
        }
      }
    },
    "definitions": {
      "Processor": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["CPU", "GPU", "TPU"]
          },
          "memory": {
            "$ref": "#/definitions/Memory"
          },
          "cache": {
            "$ref": "#/definitions/Cache"
          }
        }
      },
      "Memory": {
        "type": "object",
        "properties": {
          "capacity": {
            "type": "integer"
          },
          "type": {
            "type": "string"
          },
          "configuration": {
            "$ref": "#/definitions/Configuration"
          }
        }
      },
      "Cache": {
        "type": "object",
        "properties": {
          "level": {
            "type": "integer"
          },
          "size": {
            "type": "integer"
          }
        }
      },
      "Storage": {
        "type": "object",
        "properties": {
          "primary": {
            "$ref": "#/definitions/Drive"
          },
          "backup": {
            "$ref": "#/definitions/Drive"
          }
        }
      },
      "Drive": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["SSD", "HDD", "NVMe"]
          },
          "capacity": {
            "type": "integer"
          },
          "interface": {
            "$ref": "#/definitions/Interface"
          }
        }
      },
      "Interface": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string"
          },
          "speed": {
            "type": "integer"
          },
          "permissions": {
            "$ref": "#/definitions/Permission"
          }
        }
      },
      "Configuration": {
        "type": "object",
        "properties": {
          "mode": {
            "type": "string"
          },
          "parameters": {
            "type": "object",
            "additionalProperties": true
          }
        }
      },
      "Permission": {
        "type": "object",
        "properties": {
          "level": {
            "type": "string",
            "enum": ["read", "write", "admin"]
          },
          "scope": {
            "type": "string"
          }
        }
      }
    }
  };
  
  await Deno.writeTextFile(filePath, JSON.stringify(schema, null, 2));
}

/**
 * 循環参照を持つテスト用スキーマを作成する
 * 
 * @param filePath スキーマを保存するファイルパス
 */
async function createCircularSchema(filePath: string): Promise<void> {
  const schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CircularDependencySchema",
    "description": "循環参照を持つテスト用スキーマ",
    "type": "object",
    "properties": {
      "root": {
        "$ref": "#/definitions/NodeA"
      }
    },
    "definitions": {
      "NodeA": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "next": {
            "$ref": "#/definitions/NodeB"
          }
        }
      },
      "NodeB": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "next": {
            "$ref": "#/definitions/NodeC"
          }
        }
      },
      "NodeC": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "next": {
            "$ref": "#/definitions/NodeA"  // 循環参照
          }
        }
      }
    }
  };
  
  await Deno.writeTextFile(filePath, JSON.stringify(schema, null, 2));
}

/**
 * 依存関係解析のテストを実行する
 * 
 * @param schemaPath スキーマファイルのパス
 * @param format 出力形式
 * @param tempDir 一時ディレクトリのパス
 * @returns テスト結果
 */
async function testDependencyAnalysis(
  schemaPath: string,
  format: string,
  tempDir: string
): Promise<TestResult> {
  const outputPath = `${tempDir}/output-${format}.${format === "json" ? "json" : format === "mermaid" ? "md" : "txt"}`;
  
  try {
    // depsコマンドを実行
    const cmd = new Deno.Command("./cli.ts", {
      args: [
        "deps",
        "--schema", schemaPath,
        "--format", format,
        "--output", outputPath
      ],
      //cwd: "..",  // testディレクトリからの相対パス
      stdout: "piped",
      stderr: "piped"
    });
    
    const output = await cmd.output();
    const stdout = new TextDecoder().decode(output.stdout);
    const stderr = new TextDecoder().decode(output.stderr);
    
    // 出力ファイルの存在確認
    const fileExists = await exists(outputPath);
    if (!fileExists) {
      return {
        passed: false,
        message: "出力ファイルが生成されませんでした",
        details: stderr || stdout
      };
    }
    
    // 出力ファイルの内容確認
    const content = await Deno.readTextFile(outputPath);
    
    // 形式ごとの検証
    if (format === "json") {
      try {
        const json = JSON.parse(content);
        if (!json.nodes || !Array.isArray(json.nodes) || json.nodes.length === 0) {
          return {
            passed: false,
            message: "JSONにノード情報が含まれていません",
            details: content
          };
        }
        if (!json.edges || !Array.isArray(json.edges)) {
          return {
            passed: false,
            message: "JSONにエッジ情報が含まれていません",
            details: content
          };
        }
        return {
          passed: true,
          message: `${json.nodes.length}ノード, ${json.edges.length}エッジが検出されました`,
          details: content
        };
      } catch (error) {
        return {
          passed: false,
          message: "JSONの解析に失敗しました: " + error.message,
          details: content
        };
      }
    } else if (format === "mermaid") {
      // Mermaidグラフ構文の基本チェック
      if (!content.includes("graph ")) {
        return {
          passed: false,
          message: "Mermaid形式が不正です",
          details: content
        };
      }
      return {
        passed: true,
        message: `Mermaidグラフが正常に生成されました (${content.split("\n").length}行)`,
        details: content
      };
    } else {
      // tree形式は単純に内容の有無をチェック
      if (content.trim().length === 0) {
        return {
          passed: false,
          message: "空の出力が生成されました",
          details: content
        };
      }
      return {
        passed: true,
        message: `ツリー形式の出力が生成されました (${content.split("\n").length}行)`,
        details: content
      };
    }
  } catch (error) {
    return {
      passed: false,
      message: `コマンド実行中にエラーが発生しました: ${error.message}`
    };
  }
}

/**
 * 循環参照検出のテスト
 * 
 * @param schemaPath 循環参照を含むスキーマファイルのパス
 * @param tempDir 一時ディレクトリのパス
 * @returns テスト結果
 */
async function testCircularReference(
  schemaPath: string,
  tempDir: string
): Promise<TestResult> {
  const outputPath = `${tempDir}/output-circular.json`;
  
  try {
    // JSONとして出力（循環参照情報を含む）
    const cmd = new Deno.Command("./cli.ts", {
      args: [
        "deps",
        "--schema", schemaPath,
        "--format", "json",
        "--output", outputPath
      ],
      //cwd: "..",  // testディレクトリからの相対パス
      stdout: "piped",
      stderr: "piped"
    });
    
    await cmd.output();
    
    // 出力ファイルの存在確認
    const fileExists = await exists(outputPath);
    if (!fileExists) {
      return {
        passed: false,
        message: "出力ファイルが生成されませんでした"
      };
    }
    
    // 出力ファイルの内容確認
    const content = await Deno.readTextFile(outputPath);
    
    try {
      const json = JSON.parse(content);
      
      // 循環参照が検出されているか確認
      const circularEdges = json.edges.filter((edge: any) => 
        edge.properties && edge.properties.isCircular === true
      );
      
      if (circularEdges.length > 0) {
        return {
          passed: true,
          message: `${circularEdges.length}件の循環参照が正しく検出されました`,
          details: `循環エッジ: ${JSON.stringify(circularEdges)}`
        };
      } else {
        return {
          passed: false,
          message: "循環参照が検出されませんでした",
          details: content
        };
      }
    } catch (error) {
      return {
        passed: false,
        message: "JSONの解析に失敗しました: " + error.message,
        details: content
      };
    }
  } catch (error) {
    return {
      passed: false,
      message: `コマンド実行中にエラーが発生しました: ${error.message}`
    };
  }
}

// メイン関数の実行
if (import.meta.main) {
  await main();
}
