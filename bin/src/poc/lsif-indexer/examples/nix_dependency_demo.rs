use lsp::adapter::nixd::NixdAdapter;
use lsp::lsp_client::LspClient;
use std::path::Path;

fn main() -> anyhow::Result<()> {
    // 現在のプロジェクト（LSIF Indexer自体）のNix依存関係を解析
    let project_root = std::env::current_dir()?;
    let project_root = project_root.as_path();
    
    println!("=== Nix Dependency Analysis Demo ===");
    println!("Project: {}", project_root.display());
    println!();
    
    // NixdAdapterとLspClientを初期化
    let adapter = NixdAdapter::new();
    let mut client = LspClient::new(Box::new(NixdAdapter::new()))?;
    
    // LSPサーバーを初期化
    println!("Initializing nixd LSP server...");
    client.initialize(project_root)?;
    
    // flake.nixを解析
    let flake_path = project_root.join("flake.nix");
    if flake_path.exists() {
        println!("Analyzing flake.nix...");
        
        // ファイルを開く
        client.open_document(&flake_path)?;
        
        // シンボルを取得
        println!("\n📦 Symbols in flake.nix:");
        match adapter.get_nix_symbols(&mut client, &flake_path) {
            Ok(symbols) => {
                for symbol in &symbols {
                    println!("  - {} (line {})", symbol.name, symbol.range.start.line + 1);
                }
            }
            Err(e) => eprintln!("  Error getting symbols: {}", e),
        }
        
        // flake inputsを静的解析でも取得
        println!("\n📥 Flake inputs (static analysis):");
        let content = std::fs::read_to_string(&flake_path)?;
        let inputs = adapter.parse_flake_inputs(&content);
        for (name, url) in &inputs {
            println!("  - {}: {}", name, url);
        }
    }
    
    // 依存関係グラフを構築
    println!("\n🔗 Building dependency graph...");
    match adapter.build_dependency_graph(&mut client, project_root) {
        Ok(dependencies) => {
            if dependencies.is_empty() {
                println!("  No cross-file dependencies found via LSP");
            } else {
                for (file, deps) in &dependencies {
                    println!("\n  {}:", file);
                    for dep in deps {
                        println!("    └─> {}", dep);
                    }
                }
            }
        }
        Err(e) => eprintln!("  Error building dependency graph: {}", e),
    }
    
    // クリーンアップ
    println!("\nShutting down LSP server...");
    client.shutdown()?;
    
    println!("✅ Demo completed successfully!");
    
    Ok(())
}