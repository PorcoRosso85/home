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
          cp ${./pyright_json_api.py} $TEST_DIR/pyright_json_api.py
          
          cd $TEST_DIR
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 test_pyright_api.py
          
          # Clean up
          rm -rf $TEST_DIR
        '';
        
        # JSON-RPC API for pyright
        pyrightJson = pkgs.writeShellScriptBin "pyright-json" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          if [ -t 0 ]; then
            # Interactive mode - show usage
            cat << 'EOF'
Pyright JSON-RPC API

Usage: echo '<json>' | pyright-json

Examples:
  # Initialize
  echo '{"method": "initialize", "params": {"rootPath": "."}}' | pyright-json
  
  # Get diagnostics
  echo '{"method": "textDocument/diagnostics", "params": {"file": "test.py"}}' | pyright-json
  
  # Go to definition
  echo '{"method": "textDocument/definition", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | pyright-json
  
  # Find references
  echo '{"method": "textDocument/references", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | pyright-json

Available methods:
  - initialize: Initialize LSP server and show capabilities
  - textDocument/diagnostics: Get type errors and warnings
  - textDocument/definition: Find where a symbol is defined
  - textDocument/references: Find all uses of a symbol
EOF
            exit 0
          fi
          
          # Run the JSON API
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 ${./pyright_json_api.py}
        '';
        
        # Minimal LSP client for basic operations
        pyrightLsp = pkgs.writeShellScriptBin "pyright-lsp" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          cat > /tmp/pyright-minimal-lsp.py << 'EOF'
import sys
import json
import subprocess
import os

def send_request(proc, request):
    content = json.dumps(request)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    proc.stdin.write((header + content).encode())
    proc.stdin.flush()

def read_response(proc):
    headers = {}
    while True:
        line = proc.stdout.readline().decode().strip()
        if not line:
            break
        key, value = line.split(": ", 1)
        headers[key] = value
    
    content_length = int(headers.get("Content-Length", 0))
    if content_length > 0:
        content = proc.stdout.read(content_length).decode()
        return json.loads(content)
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: pyright-lsp <command> [args...]")
        print("Commands:")
        print("  init <workspace>     Initialize LSP server")
        print("  check <file>         Get diagnostics for file")
        print("  definition <file> <line> <col>  Go to definition")
        print("  references <file> <line> <col>  Find references")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Start pyright LSP server
    proc = subprocess.Popen(
        ["pyright-langserver", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        if command == "init":
            workspace = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
            
            # Initialize
            send_request(proc, {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": f"file://{os.path.abspath(workspace)}",
                    "capabilities": {}
                }
            })
            
            response = read_response(proc)
            print(json.dumps(response.get("result", {}).get("capabilities", {}), indent=2))
            
        elif command == "check":
            file_path = os.path.abspath(sys.argv[2])
            
            # Initialize first
            send_request(proc, {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": f"file://{os.path.dirname(file_path)}",
                    "capabilities": {}
                }
            })
            read_response(proc)
            
            # Send initialized
            send_request(proc, {
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {}
            })
            
            # Open document
            with open(file_path, 'r') as f:
                content = f.read()
            
            send_request(proc, {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": f"file://{file_path}",
                        "languageId": "python",
                        "version": 1,
                        "text": content
                    }
                }
            })
            
            # Read diagnostics
            while True:
                response = read_response(proc)
                if response and response.get("method") == "textDocument/publishDiagnostics":
                    diagnostics = response.get("params", {}).get("diagnostics", [])
                    if diagnostics:
                        print("Diagnostics found:")
                        for diag in diagnostics:
                            print(f"  Line {diag['range']['start']['line'] + 1}: {diag['message']}")
                    else:
                        print("No issues found!")
                    break
                    
        elif command in ["definition", "references"]:
            if len(sys.argv) < 5:
                print(f"Usage: pyright-lsp {command} <file> <line> <column>")
                sys.exit(1)
            
            file_path = os.path.abspath(sys.argv[2])
            line = int(sys.argv[3]) - 1  # Convert to 0-based
            col = int(sys.argv[4]) - 1
            
            # Initialize
            send_request(proc, {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": f"file://{os.path.dirname(file_path)}",
                    "capabilities": {}
                }
            })
            read_response(proc)
            
            # Send initialized
            send_request(proc, {
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {}
            })
            
            # Open document
            with open(file_path, 'r') as f:
                content = f.read()
            
            send_request(proc, {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": f"file://{file_path}",
                        "languageId": "python",
                        "version": 1,
                        "text": content
                    }
                }
            })
            
            # Request definition or references
            method = f"textDocument/{command}"
            send_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": {
                    "textDocument": {"uri": f"file://{file_path}"},
                    "position": {"line": line, "character": col},
                    "context": {"includeDeclaration": True} if command == "references" else None
                }
            })
            
            response = read_response(proc)
            result = response.get("result", [])
            
            if result:
                print(f"{command.capitalize()} found:")
                for loc in result:
                    uri = loc["uri"].replace("file://", "")
                    start = loc["range"]["start"]
                    print(f"  {uri}:{start['line'] + 1}:{start['character'] + 1}")
            else:
                print(f"No {command} found.")
                
    finally:
        proc.terminate()

if __name__ == "__main__":
    main()
EOF
          
          PATH="${pkgs.pyright}/bin:$PATH" ${pkgs.python3}/bin/python3 /tmp/pyright-minimal-lsp.py "$@"
        '';
        
      in
      {
        packages = {
          default = pyrightJson;
          check = pyrightCheck;
          lsp = pyrightLsp;
          json = pyrightJson;
          test = testRunner;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pyright
            python3
          ];
          
          shellHook = ''
            echo "Minimal Pyright LSP Environment"
            echo ""
            echo "Available commands:"
            echo "  nix run .#check -- <file.py>                   # Run pyright diagnostics"
            echo "  nix run .#json                                 # Show JSON-RPC API usage (recommended)"
            echo "  nix run .#lsp -- init <workspace>              # Initialize LSP server"
            echo "  nix run .#lsp -- check <file.py>               # Get diagnostics via LSP"
            echo "  nix run .#lsp -- definition <file> <line> <col># Go to definition"
            echo "  nix run .#lsp -- references <file> <line> <col># Find references"
          '';
        };
        
        apps = {
          default = flake-utils.lib.mkApp {
            drv = pyrightJson;
          };
          
          check = flake-utils.lib.mkApp {
            drv = pyrightCheck;
          };
          
          lsp = flake-utils.lib.mkApp {
            drv = pyrightLsp;
          };
          
          json = flake-utils.lib.mkApp {
            drv = pyrightJson;
          };
          
          test = flake-utils.lib.mkApp {
            drv = testRunner;
          };
        };
      }
    );
}