use crate::fallback_indexer::*;
use std::path::Path;

#[test]
fn debug_nix_extraction() {
    let nix_code = r#"
{
  description = "A flake for testing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        myFunction = x: x + 1;
      in
      {
        devShells.default = pkgs.mkShell {};
      });
}
"#;

    let indexer = FallbackIndexer::new(FallbackLanguage::Nix);
    let lines: Vec<&str> = nix_code.lines().collect();
    let symbols = indexer.extract_nix_symbols(&lines).unwrap();
    
    for symbol in &symbols {
        println!("Found symbol: '{}' - kind: {:?}", symbol.name, symbol.kind);
    }
    
    assert!(!symbols.is_empty());
}
