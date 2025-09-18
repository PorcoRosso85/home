use lsp::adapter::nixd::NixdAdapter;
use lsp::adapter::language::LanguageAdapter;

#[test]
fn test_nix_adapter_creation() {
    let adapter = NixdAdapter::new();
    assert_eq!(adapter.language_id(), "nix");
    assert_eq!(adapter.supported_extensions(), vec!["nix"]);
}

#[test]
fn test_nix_adapter_lsp_spawn() {
    let adapter = NixdAdapter::new();
    // LSPコマンドのスポーンは実際のnixdが必要なのでテストしない
    // ただし、メソッドが存在することは確認
    let _ = adapter.spawn_lsp_command();
}

#[test]
fn test_nix_adapter_patterns() {
    let adapter = NixdAdapter::new();
    
    // 最小実装では空のパターンを返す
    assert_eq!(adapter.definition_patterns().len(), 0);
    
    // リファレンスパターンは基本的な単語境界マッチ
    let pattern = adapter.build_reference_pattern("nixpkgs", &lsif_core::SymbolKind::Variable);
    assert!(pattern.contains("nixpkgs"));
}