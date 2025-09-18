{
  description = "LSIF Indexer with Nix/flake dependency analysis support";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        rustDeps = with pkgs; [
          rustc
          cargo
          rust-analyzer
          rustfmt
          clippy
        ];
        
        lspServers = with pkgs; [
          # Nix LSP (required for NixdAdapter)
          nixd
          
          # Other LSPs for testing
          rust-analyzer
          nodePackages.typescript-language-server
          python3Packages.python-lsp-server
          gopls
        ];
        
        devTools = with pkgs; [
          pkg-config
          openssl
          cargo-watch
          cargo-nextest
          tokio-console
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = rustDeps ++ lspServers ++ devTools;
          
          shellHook = ''
            echo "LSIF Indexer Development Environment"
            echo "Available LSPs:"
            echo "  - nixd (Nix Language Server)"
            echo "  - rust-analyzer"
            echo "  - typescript-language-server"
            echo "  - pylsp"
            echo "  - gopls"
            echo ""
            echo "Run 'cargo build' to build the indexer"
            echo "Run 'cargo test' to run tests"
          '';
          
          # Environment variables for LSP paths
          NIXD_PATH = "${pkgs.nixd}/bin/nixd";
          RUST_ANALYZER_PATH = "${pkgs.rust-analyzer}/bin/rust-analyzer";
        };
        
        # Package definition for the indexer itself
        packages.default = pkgs.rustPlatform.buildRustPackage {
          pname = "lsif-indexer";
          version = "0.1.0";
          src = ./.;
          cargoSha256 = pkgs.lib.fakeSha256;
        };
      });
}