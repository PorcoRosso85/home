{
  description = "LSP CLI wrapper using LSMCP approach";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Reference external LSMCP repository
    lsmcp-src = {
      url = "github:mizchi/lsmcp/35da2b193b0fc1326ba6bebcff62fcf0cbeac1b5";
      flake = false;
    };
  };
  
  outputs = { self, nixpkgs, lsmcp-src }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      
      # Base LSP runner script
      mkLspRunner = { name, lspCmd }: pkgs.writeShellScriptBin name ''
        #!${pkgs.bash}/bin/bash
        export LSMCP_SOURCE="${lsmcp-src}"
        export DEBUG=''${DEBUG:-}
        
        # Ensure LSP server is in PATH
        PATH="${lspCmd}:$PATH"
        
        # Run CLI with Node.js experimental TypeScript support
        exec ${pkgs.nodejs}/bin/node \
          --experimental-strip-types \
          ${./cli.ts} \
          "$@"
      '';
      
    in {
      packages.${system} = {
        # Default package
        default = self.packages.${system}.lsp-python;
        
        # Python LSP using pyright
        lsp-python = mkLspRunner {
          name = "lsp-python";
          lspCmd = "${pkgs.pyright}/bin";
        };
        
        # TypeScript LSP
        lsp-typescript = mkLspRunner {
          name = "lsp-typescript";
          lspCmd = "${pkgs.nodePackages.typescript-language-server}/bin";
        };
        
        # Rust LSP
        lsp-rust = mkLspRunner {
          name = "lsp-rust";
          lspCmd = "${pkgs.rust-analyzer}/bin";
        };
        
        # Test runner for all LSP features
        test-lsp-features = pkgs.writeShellScriptBin "test-lsp-features" ''
          #!${pkgs.bash}/bin/bash
          set -e
          
          echo "=== Testing LSP Features via Nix Flake ==="
          echo ""
          
          # Create test file
          cat > /tmp/test_lsp.py << 'EOF'
class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x: int, y: int) -> int:
        return x + y

calc = Calculator()  # Line 8
result = calc.add(10, 20)  # Line 9
print(result)
EOF
          
          echo "1. Testing findReferences..."
          ${self.packages.${system}.lsp-python}/bin/lsp-python '
            const refs = await findReferences("/tmp/test_lsp.py", 8, "calc");
            console.log("Found " + refs.length + " references:");
            refs.forEach(r => console.log("  - Line " + r.line));
          '
          
          echo ""
          echo "2. Testing getDefinition..."
          ${self.packages.${system}.lsp-python}/bin/lsp-python '
            const defs = await getDefinition("/tmp/test_lsp.py", 9, "add");
            console.log("Found definition at line " + (defs[0] ? defs[0].line : "unknown"));
          '
          
          echo ""
          echo "3. Testing getDocumentSymbols..."
          ${self.packages.${system}.lsp-python}/bin/lsp-python '
            const symbols = await getDocumentSymbols("/tmp/test_lsp.py");
            console.log("Found " + symbols.length + " symbols:");
            symbols.slice(0, 5).forEach(s => console.log("  - " + s.name + " (kind: " + s.kind + ")"));
          '
          
          echo ""
          echo "4. Testing hover..."
          ${self.packages.${system}.lsp-python}/bin/lsp-python '
            const info = await hover("/tmp/test_lsp.py", 8, 0);
            console.log("Hover info: " + (info || "none"));
          '
          
          rm -f /tmp/test_lsp.py
          echo ""
          echo "✅ All tests completed!"
        '';
      };
      
      # Development shell
      devShell.${system} = pkgs.mkShell {
        buildInputs = with pkgs; [
          nodejs
          pyright
          nodePackages.typescript-language-server
          rust-analyzer
        ];
        
        shellHook = ''
          echo "LSP CLI Development Environment"
          echo ""
          echo "Available commands:"
          echo "  nix run .#lsp-python"
          echo "  nix run .#lsp-typescript"
          echo "  nix run .#lsp-rust"
          echo "  nix run .#test-lsp-features"
          echo ""
          echo "LSMCP source: ${lsmcp-src}"
        '';
      };
    };
}