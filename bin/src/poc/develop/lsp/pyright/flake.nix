{
  description = "Pyright LSP CLI wrapper";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # CLI wrapper for pyright LSP
        pyrightCliWrapper = pkgs.writeShellScriptBin "pyright-cli" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          # Compile TypeScript wrapper
          ${pkgs.esbuild}/bin/esbuild \
            lsmcp-cli-wrapper.ts \
            --bundle \
            --platform=node \
            --outfile=/tmp/pyright-cli-wrapper.js
          
          # Run with pyright in PATH
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.nodejs}/bin/node /tmp/pyright-cli-wrapper.js "$@"
        '';
        
        # Test scripts
        testFindRefs = pkgs.writeShellScriptBin "test-find-refs" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Testing Find References ==="
          ${pyrightCliWrapper}/bin/pyright-cli find-refs test_good.py 7 7
        '';
        
        testRename = pkgs.writeShellScriptBin "test-rename" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Testing Rename Symbol ==="
          ${pyrightCliWrapper}/bin/pyright-cli rename test_good.py 7 7 ComputeEngine
        '';
        
        # Direct Python LSP interface
        pythonLsp = pkgs.writeShellScriptBin "python-lsp" ''
          #!${pkgs.bash}/bin/bash
          cd ${./.}
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 direct_lsp.py "$@"
        '';
        
        # Simple pyright test
        pyrightTest = pkgs.writeShellScriptBin "pyright-test" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Direct pyright test ==="
          echo ""
          
          echo "1. Check pyright version:"
          ${pkgs.pyright}/bin/pyright --version
          echo ""
          
          echo "2. Run diagnostics on test_example.py:"
          if [ -f "${./.}/test_example.py" ]; then
            ${pkgs.pyright}/bin/pyright ${./.}/test_example.py
          else
            echo "Creating test file..."
            cat > /tmp/test_pyright.py << 'EOF'
class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

calc = Calculator()
result = calc.add(10, 20)
# Error: typo
calc.addd(1, 2)
EOF
            ${pkgs.pyright}/bin/pyright /tmp/test_pyright.py
          fi
          echo ""
          
          echo "3. pyright-langserver requires --stdio for LSP mode"
        '';
        
        # Direct pyright usage test
        pyrightDirect = pkgs.writeShellScriptBin "pyright-direct" ''
          #!${pkgs.bash}/bin/bash
          cd ${./.}
          PYRIGHT_PATH="${pkgs.pyright}/bin/pyright-langserver" ${pkgs.nodejs}/bin/node pyright_direct.js
        '';
        
        # Test LSP capabilities
        testCapabilities = pkgs.writeShellScriptBin "test-capabilities" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Testing Pyright LSP Capabilities ==="
          cd /home/nixos/bin/src/poc/develop/lsp/pyright
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 lsp_capabilities_test.py
        '';
        
        # Run pytest suite
        testSuite = pkgs.writeShellScriptBin "test-suite" ''
          #!${pkgs.bash}/bin/bash
          echo "=== Running Pyright LSP Test Suite ==="
          cd /home/nixos/bin/src/poc/develop/lsp/pyright
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3.withPackages (ps: [ ps.pytest ])}/bin/pytest -v test_pyright_lsp.py
        '';
        
      in
      {
        packages = {
          default = pythonLsp;
          pyright-cli = pyrightCliWrapper;
          test-find-refs = testFindRefs;
          test-rename = testRename;
          python-lsp = pythonLsp;
          pyright-test = pyrightTest;
          pyright-direct = pyrightDirect;
          test-capabilities = testCapabilities;
          test-suite = testSuite;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            pyright
            esbuild
            python3
          ];
          
          shellHook = ''
            echo "Pyright LSP CLI Development Environment"
            echo ""
            echo "Available commands:"
            echo "  pyright-cli find-refs <file> <line> <column>"
            echo "  pyright-cli rename <file> <line> <column> <new-name>"
            echo ""
            echo "Test commands:"
            echo "  nix run .#test-find-refs"
            echo "  nix run .#test-rename"
          '';
        };
        
        apps = {
          default = flake-utils.lib.mkApp {
            drv = pyrightCliWrapper;
          };
          
          test-find-refs = flake-utils.lib.mkApp {
            drv = testFindRefs;
          };
          
          test-rename = flake-utils.lib.mkApp {
            drv = testRename;
          };
          
          test-capabilities = flake-utils.lib.mkApp {
            drv = testCapabilities;
          };
          
          test-suite = flake-utils.lib.mkApp {
            drv = testSuite;
          };
          
          python = flake-utils.lib.mkApp {
            drv = pythonLsp;
          };
        };
      }
    );
}