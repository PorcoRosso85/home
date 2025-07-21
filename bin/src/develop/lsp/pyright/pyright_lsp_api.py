#!/usr/bin/env python3
"""
統一的なJSON-RPCベースのPyright LSP API

Usage:
  echo '{"method": "initialize", "params": {"rootPath": "."}}' | python pyright_json_api.py
  echo '{"method": "textDocument/definition", "params": {"file": "test.py", "position": {"line": 10, "character": 5}}}' | python pyright_json_api.py
"""

import sys
import json
import subprocess
import os
from typing import Dict, Any, Optional


class PyrightLSPClient:
    def __init__(self):
        self.proc = None
        self.initialized = False
        self.root_uri = None
        
    def start_server(self):
        """Start pyright LSP server"""
        self.proc = subprocess.Popen(
            ["pyright-langserver", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
    def send_request(self, request: Dict[str, Any]) -> None:
        """Send request to LSP server"""
        content = json.dumps(request)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        self.proc.stdin.write((header + content).encode())
        self.proc.stdin.flush()
        
    def read_response(self) -> Optional[Dict[str, Any]]:
        """Read response from LSP server"""
        headers = {}
        while True:
            line = self.proc.stdout.readline().decode().strip()
            if not line:
                break
            key, value = line.split(": ", 1)
            headers[key] = value
        
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = self.proc.stdout.read(content_length).decode()
            return json.loads(content)
        return None
        
    def initialize(self, root_path: str = ".") -> Dict[str, Any]:
        """Initialize LSP server"""
        self.root_uri = f"file://{os.path.abspath(root_path)}"
        
        self.send_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": self.root_uri,
                "capabilities": {}
            }
        })
        
        response = self.read_response()
        
        # Send initialized notification
        self.send_request({
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        })
        
        self.initialized = True
        return response.get("result", {}).get("capabilities", {})
        
    def ensure_initialized(self, file_path: Optional[str] = None):
        """Ensure server is initialized"""
        if not self.initialized:
            root_path = os.path.dirname(file_path) if file_path else "."
            self.initialize(root_path)
            
    def open_document(self, file_path: str) -> None:
        """Open document in LSP server"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        uri = f"file://{os.path.abspath(file_path)}"
        
        self.send_request({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": content
                }
            }
        })
        
    def get_diagnostics(self, file_path: str) -> list:
        """Get diagnostics for a file"""
        self.ensure_initialized(file_path)
        self.open_document(file_path)
        
        # Wait for diagnostics
        diagnostics = []
        while True:
            response = self.read_response()
            if response and response.get("method") == "textDocument/publishDiagnostics":
                diagnostics = response.get("params", {}).get("diagnostics", [])
                break
                
        return diagnostics
        
    def get_definition(self, file_path: str, line: int, character: int) -> list:
        """Get definition location"""
        self.ensure_initialized(file_path)
        self.open_document(file_path)
        
        uri = f"file://{os.path.abspath(file_path)}"
        
        self.send_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character}
            }
        })
        
        response = self.read_response()
        return response.get("result", [])
        
    def get_references(self, file_path: str, line: int, character: int) -> list:
        """Get all references"""
        self.ensure_initialized(file_path)
        self.open_document(file_path)
        
        uri = f"file://{os.path.abspath(file_path)}"
        
        self.send_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "textDocument/references",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True}
            }
        })
        
        response = self.read_response()
        return response.get("result", [])


def main():
    """Main entry point for JSON-RPC API"""
    # Read JSON from stdin
    input_data = sys.stdin.read()
    
    try:
        request = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "error": f"Invalid JSON: {str(e)}",
            "expected": {
                "method": "string",
                "params": "object"
            }
        }), file=sys.stderr)
        sys.exit(1)
        
    # Validate request
    if not isinstance(request, dict) or "method" not in request:
        print(json.dumps({
            "error": "Invalid request format",
            "expected": {
                "method": "string",
                "params": "object (optional)"
            }
        }), file=sys.stderr)
        sys.exit(1)
        
    method = request["method"]
    params = request.get("params", {})
    
    # Create client and start server
    client = PyrightLSPClient()
    client.start_server()
    
    try:
        result = None
        
        if method == "initialize":
            root_path = params.get("rootPath", ".")
            result = {
                "capabilities": client.initialize(root_path)
            }
            
        elif method == "textDocument/diagnostics":
            file_path = params.get("file")
            if not file_path:
                raise ValueError("Missing required parameter: file")
                
            diagnostics = client.get_diagnostics(file_path)
            result = {
                "diagnostics": [
                    {
                        "line": d["range"]["start"]["line"] + 1,
                        "column": d["range"]["start"]["character"] + 1,
                        "message": d["message"],
                        "severity": d.get("severity", 1)
                    }
                    for d in diagnostics
                ]
            }
            
        elif method == "textDocument/definition":
            file_path = params.get("file")
            position = params.get("position", {})
            
            if not file_path:
                raise ValueError("Missing required parameter: file")
            if "line" not in position or "character" not in position:
                raise ValueError("Missing required position parameters: line, character")
                
            locations = client.get_definition(
                file_path,
                position["line"] - 1,  # Convert to 0-based
                position["character"] - 1
            )
            
            result = {
                "definitions": [
                    {
                        "file": loc["uri"].replace("file://", ""),
                        "line": loc["range"]["start"]["line"] + 1,
                        "column": loc["range"]["start"]["character"] + 1
                    }
                    for loc in locations
                ]
            }
            
        elif method == "textDocument/references":
            file_path = params.get("file")
            position = params.get("position", {})
            
            if not file_path:
                raise ValueError("Missing required parameter: file")
            if "line" not in position or "character" not in position:
                raise ValueError("Missing required position parameters: line, character")
                
            locations = client.get_references(
                file_path,
                position["line"] - 1,  # Convert to 0-based
                position["character"] - 1
            )
            
            result = {
                "references": [
                    {
                        "file": loc["uri"].replace("file://", ""),
                        "line": loc["range"]["start"]["line"] + 1,
                        "column": loc["range"]["start"]["character"] + 1
                    }
                    for loc in locations
                ]
            }
            
        else:
            raise ValueError(f"Unknown method: {method}")
            
        # Output result
        print(json.dumps({
            "success": True,
            "result": result
        }, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(1)
        
    finally:
        if client.proc:
            client.proc.terminate()


if __name__ == "__main__":
    main()