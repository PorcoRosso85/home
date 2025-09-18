{
  description = "Minimal Pyright LSP functionality based on POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Simple pyright diagnostics wrapper
        pyrightCheck = pkgs.writeShellScriptBin "pyright-check" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          if [ $# -eq 0 ]; then
            echo "Usage: pyright-check <file.py>"
            exit 1
          fi
          
          ${pkgs.pyright}/bin/pyright "$@"
        '';
        
        # Test runner
        testRunner = pkgs.writeShellScriptBin "test-runner" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          echo "Running Pyright API Tests..."
          cd ${./.}
          
          # Copy test files to a writable directory
          export TEST_DIR=$(mktemp -d)
          cp ${./test_pyright_api.py} $TEST_DIR/test_pyright_api.py
          cp ${./pyright_lsp_api.py} $TEST_DIR/pyright_lsp_api.py
          
          cd $TEST_DIR
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 test_pyright_api.py
          
          # Clean up
          rm -rf $TEST_DIR
        '';
        
        # LSP API for pyright
        pyrightLspApi = pkgs.writeShellScriptBin "pyright-lsp-api" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          if [ -t 0 ]; then
            # Interactive mode - show usage
            cat << 'EOF'
Pyright LSP API

Usage: echo '<json>' | pyright-lsp-api

Examples:
  # Initialize
  echo '{"method": "initialize", "params": {"rootPath": "."}}' | pyright-lsp-api
  
  # Get diagnostics
  echo '{"method": "textDocument/diagnostics", "params": {"file": "test.py"}}' | pyright-lsp-api
  
  # Go to definition
  echo '{"method": "textDocument/definition", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | pyright-lsp-api
  
  # Find references
  echo '{"method": "textDocument/references", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | pyright-lsp-api

Available methods:
  - initialize: Initialize LSP server and show capabilities
  - textDocument/diagnostics: Get type errors and warnings
  - textDocument/definition: Find where a symbol is defined
  - textDocument/references: Find all uses of a symbol
EOF
            exit 0
          fi
          
          # Run the JSON API
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 ${./pyright_lsp_api.py}
        '';
        
      in
      {
        packages = {
          default = pyrightLspApi;  # Main library package
          check = pyrightCheck;
          lsp = pyrightLspApi;
          test = testRunner;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pyright
            python3
            jq
          ];
          
          shellHook = ''
            echo "Minimal Pyright LSP Environment"
            echo ""
            echo "Pyright LSP Development Shell"
            echo ""
            echo "利用可能なコマンド:"
            echo "  nix run .         # アプリ一覧表示"
            echo "  nix run .#check   # Pyright直接実行"
            echo "  nix run .#lsp     # LSP APIアクセス"
            echo "  nix run .#test    # テスト実行"
            echo "  nix run .#readme  # README表示"
          '';
        };
        
        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              sortedAppNames = builtins.sort (a: b: a < b) appNames;
              helpText = ''
                Pyright LSP - Minimal Implementation
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") sortedAppNames)}
                
                詳細は README.md を参照してください。
              '';
            in "${pkgs.writeShellScript "show-apps" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          check = flake-utils.lib.mkApp {
            drv = pyrightCheck;
          };
          
          lsp = flake-utils.lib.mkApp {
            drv = pyrightLspApi;
          };
          
          test = flake-utils.lib.mkApp {
            drv = testRunner;
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''cat ${./README.md}''}";
          };
        };
      }
    );
}