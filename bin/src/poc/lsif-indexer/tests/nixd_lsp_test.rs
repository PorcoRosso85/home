use lsp::adapter::nixd::NixdAdapter;
use lsp::adapter::language::LanguageAdapter;

#[test]
fn test_nixd_lsp_server_starts() {
    let adapter = NixdAdapter::new();
    
    let server = adapter.spawn_lsp_command();
    assert!(server.is_ok(), "nixd LSP server should start successfully");
    
    if let Ok(mut child) = server {
        // Verify the process is actually running
        let pid = child.id();
        assert!(pid > 0, "nixd LSP process should have valid PID: {}", pid);
        
        // Give it a moment to start up properly
        std::thread::sleep(std::time::Duration::from_millis(100));
        
        // Clean shutdown
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[test] 
fn test_nix_file_detection() {
    let adapter = NixdAdapter::new();
    // .nixファイルを検出できることを確認
    let extensions = adapter.supported_extensions();
    assert!(extensions.contains(&"nix"));
    assert_eq!(adapter.language_id(), "nix");
}