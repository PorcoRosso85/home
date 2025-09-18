{
  description = "LSP tools collection";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Reference subdirectory flakes
    lsmcp-wrapper.url = "path:./lsmcp";
    lsmcp-wrapper.inputs.nixpkgs.follows = "nixpkgs";
  };
  
  outputs = { self, nixpkgs, lsmcp-wrapper }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages.${system} = {
        # Re-export LSMCP wrapper packages
        inherit (lsmcp-wrapper.packages.${system})
          lsp-python
          lsp-typescript
          lsp-rust
          test-lsp-features;
        
        # Quick test command
        test-all = pkgs.writeShellScriptBin "test-all" ''
          echo "=== Testing All LSP Implementations ==="
          echo ""
          echo "1. Testing via LSMCP wrapper (no local clone):"
          ${lsmcp-wrapper.packages.${system}.test-lsp-features}/bin/test-lsp-features
        '';
      };
      
      # Aggregate development shell
      devShell.${system} = pkgs.mkShell {
        inputsFrom = [ lsmcp-wrapper.devShell.${system} ];
        shellHook = ''
          echo "=== LSP Development Environment ==="
          echo ""
          echo "This environment uses LSMCP from Nix store (no clone needed)"
          echo ""
          echo "Test all features:"
          echo "  nix run .#test-all"
        '';
      };
    };
}