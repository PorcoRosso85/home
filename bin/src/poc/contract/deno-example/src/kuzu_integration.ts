import { log } from "../../../log/mod.ts";

export interface KuzuDatabase {
  execute(query: string): Promise<void>;
  query?(cypher: string): Promise<any>;
}

export async function applyDdl(db: KuzuDatabase, ddlPath: string): Promise<void> {
  try {
    // DDLファイルのパスを解決
    const ddlFile = new URL(`../${ddlPath}`, import.meta.url);
    
    log("INFO", {
      uri: "contract.kuzu_integration.applyDdl",
      message: "Reading DDL file",
      ddlPath: ddlPath
    });
    
    const ddlContent = await Deno.readTextFile(ddlFile);
    
    // DDLをセミコロンで分割して実行
    const statements = ddlContent
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));
    
    log("INFO", {
      uri: "contract.kuzu_integration.applyDdl",
      message: "Executing DDL statements",
      statementCount: statements.length
    });
    
    for (const statement of statements) {
      try {
        await db.execute(statement + ';');
      } catch (error) {
        log("ERROR", {
          uri: "contract.kuzu_integration.applyDdl",
          message: "Failed to execute DDL statement",
          error: error instanceof Error ? error.message : String(error),
          statement: statement.substring(0, 100) + (statement.length > 100 ? '...' : '')
        });
        throw new Error(`DDL execution failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    
    log("INFO", {
      uri: "contract.kuzu_integration.applyDdl",
      message: "DDL applied successfully",
      ddlPath: ddlPath
    });
    
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      log("ERROR", {
        uri: "contract.kuzu_integration.applyDdl",
        message: "DDL file not found",
        ddlPath: ddlPath
      });
      throw new Error(`DDL file not found: ${ddlPath}`);
    }
    
    log("ERROR", {
      uri: "contract.kuzu_integration.applyDdl",
      message: "Failed to apply DDL",
      error: error instanceof Error ? error.message : String(error),
      ddlPath: ddlPath
    });
    throw error;
  }
}