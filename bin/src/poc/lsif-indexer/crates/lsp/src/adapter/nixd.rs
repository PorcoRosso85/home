use super::language::{DefinitionPattern, LanguageAdapter, PatternType};
use super::lsp::LspAdapter;
use anyhow::Result;
use std::process::{Command, Child, Stdio};
use lsp_types::{ClientInfo, InitializeParams, Url, WorkDoneProgressParams, WorkspaceFolder};

pub struct NixdAdapter;

impl NixdAdapter {
    pub fn new() -> Self {
        Self
    }
}

impl LanguageAdapter for NixdAdapter {
    fn language_id(&self) -> &str {
        "nix"
    }

    fn supported_extensions(&self) -> Vec<&str> {
        vec!["nix"]
    }

    fn spawn_lsp_command(&self) -> Result<std::process::Child> {
        let nixd_path = std::env::var("NIXD_PATH").unwrap_or_else(|_| "nixd".to_string());
        Ok(Command::new(nixd_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?)
    }

    fn definition_patterns(&self) -> Vec<DefinitionPattern> {
        // Nix doesn't have clear keyword-based patterns like other languages
        // Definitions are usually attribute sets and function parameters
        vec![]
    }

    fn build_reference_pattern(&self, name: &str, _kind: &lsif_core::SymbolKind) -> String {
        format!(r"\b{}\b", regex::escape(name))
    }

    fn is_definition_context(&self, line: &str, position: usize) -> bool {
        if position == 0 || position > line.len() {
            return false;
        }
        
        let before = &line[..position];
        before.trim_end().ends_with('=') || before.trim_end().ends_with(':')
    }

    fn is_in_string_or_comment(&self, line: &str, position: usize) -> bool {
        let before = &line[..position.min(line.len())];
        
        // Check for comments
        if let Some(comment_pos) = before.rfind('#') {
            if comment_pos < position {
                return true;
            }
        }
        
        // Simple string check for Nix
        false
    }
}

impl LspAdapter for NixdAdapter {
    fn spawn_command(&self) -> Result<Child> {
        self.spawn_lsp_command()
    }

    fn language_id(&self) -> &str {
        "nix"
    }

    /// Override initialization parameters for nixd with proper workspace configuration
    fn get_init_params(&self) -> InitializeParams {
        // Get current directory and ensure it's an absolute path
        let current_dir = std::env::current_dir()
            .unwrap_or_else(|_| std::path::PathBuf::from("."));
        
        // Create file:// URI from absolute path
        let workspace_uri = Url::from_file_path(&current_dir)
            .unwrap_or_else(|_| {
                // Fallback: use file:// with absolute path
                let abs_path = current_dir.canonicalize()
                    .unwrap_or(current_dir);
                Url::parse(&format!("file://{}", abs_path.display()))
                    .unwrap_or_else(|_| Url::parse("file:///tmp").unwrap())
            });

        #[allow(deprecated)]
        InitializeParams {
            process_id: Some(std::process::id()),
            root_uri: Some(workspace_uri.clone()),
            initialization_options: Some(serde_json::json!({
                "nixd": {
                    "formatting": {
                        "command": ["nixpkgs-fmt"]
                    }
                }
            })),
            capabilities: lsp_types::ClientCapabilities {
                text_document: Some(lsp_types::TextDocumentClientCapabilities {
                    document_symbol: Some(lsp_types::DocumentSymbolClientCapabilities {
                        dynamic_registration: Some(false),
                        symbol_kind: None,
                        hierarchical_document_symbol_support: Some(true),
                        tag_support: None,
                    }),
                    definition: Some(lsp_types::GotoCapability {
                        dynamic_registration: Some(false),
                        link_support: Some(false),
                    }),
                    references: Some(lsp_types::ReferenceClientCapabilities {
                        dynamic_registration: Some(false),
                    }),
                    ..Default::default()
                }),
                workspace: Some(lsp_types::WorkspaceClientCapabilities {
                    symbol: Some(lsp_types::WorkspaceSymbolClientCapabilities {
                        dynamic_registration: Some(false),
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
                ..Default::default()
            },
            trace: Some(lsp_types::TraceValue::Off),
            // Configure workspace_folders with proper file:// URI
            workspace_folders: Some(vec![WorkspaceFolder {
                uri: workspace_uri,
                name: "nixd-workspace".to_string(),
            }]),
            client_info: Some(ClientInfo {
                name: "lsif-indexer".to_string(),
                version: Some("0.1.0".to_string()),
            }),
            locale: None,
            root_path: None,
            work_done_progress_params: WorkDoneProgressParams::default(),
        }
    }
}
