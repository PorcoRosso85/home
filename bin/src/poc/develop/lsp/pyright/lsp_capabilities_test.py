#!/usr/bin/env python3
"""Test Pyright LSP capabilities using direct communication."""

import json
import subprocess
import time
from threading import Thread
import queue

class LSPClient:
    def __init__(self):
        self.proc = None
        self.response_queue = queue.Queue()
        self.request_id = 0
        
    def start(self):
        """Start pyright-langserver process."""
        self.proc = subprocess.Popen(
            ["pyright-langserver", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start reader thread
        reader_thread = Thread(target=self._read_responses)
        reader_thread.daemon = True
        reader_thread.start()
        
    def _read_responses(self):
        """Read responses from stdout."""
        while True:
            try:
                # Read header
                headers = {}
                while True:
                    line = self.proc.stdout.readline().strip()
                    if not line:
                        break
                    key, value = line.split(': ', 1)
                    headers[key] = value
                
                # Read content
                if 'Content-Length' in headers:
                    content_length = int(headers['Content-Length'])
                    content = self.proc.stdout.read(content_length)
                    response = json.loads(content)
                    self.response_queue.put(response)
            except Exception as e:
                break
    
    def send_request(self, method, params=None):
        """Send request and wait for response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_str = json.dumps(request)
        header = f"Content-Length: {len(request_str)}\r\n\r\n"
        message = header + request_str
        
        self.proc.stdin.write(message)
        self.proc.stdin.flush()
        
        # Wait for response with matching ID
        timeout = time.time() + 5  # 5 second timeout
        while time.time() < timeout:
            try:
                response = self.response_queue.get(timeout=0.1)
                if response.get("id") == self.request_id:
                    return response
                # Put back if not matching
                self.response_queue.put(response)
            except queue.Empty:
                continue
        
        return None
    
    def send_notification(self, method, params=None):
        """Send notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        notification_str = json.dumps(notification)
        header = f"Content-Length: {len(notification_str)}\r\n\r\n"
        message = header + notification_str
        
        self.proc.stdin.write(message)
        self.proc.stdin.flush()
    
    def stop(self):
        """Stop the server."""
        if self.proc:
            self.send_request("shutdown")
            self.send_notification("exit")
            self.proc.terminate()
            self.proc.wait()

def test_pyright_capabilities():
    """Test Pyright's refactoring capabilities."""
    client = LSPClient()
    client.start()
    
    try:
        # Initialize
        print("=== Initializing Pyright LSP ===")
        init_params = {
            "processId": None,
            "rootPath": "/home/nixos/bin/src/poc/develop/lsp/pyright",
            "rootUri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright",
            "capabilities": {
                "textDocument": {
                    "rename": {
                        "prepareSupport": True
                    },
                    "references": {}
                }
            }
        }
        
        response = client.send_request("initialize", init_params)
        if response and "result" in response:
            capabilities = response["result"]["capabilities"]
            
            print("\n=== Server Capabilities ===")
            print(f"Rename Provider: {capabilities.get('renameProvider', False)}")
            print(f"References Provider: {capabilities.get('referencesProvider', False)}")
            print(f"Definition Provider: {capabilities.get('definitionProvider', False)}")
            print(f"Type Definition Provider: {capabilities.get('typeDefinitionProvider', False)}")
            print(f"Hover Provider: {capabilities.get('hoverProvider', False)}")
            print(f"Completion Provider: {capabilities.get('completionProvider', False)}")
            print(f"Signature Help Provider: {capabilities.get('signatureHelpProvider', False)}")
            print(f"Document Symbol Provider: {capabilities.get('documentSymbolProvider', False)}")
            print(f"Code Action Provider: {capabilities.get('codeActionProvider', False)}")
            
            # Send initialized notification
            client.send_notification("initialized")
            
            # Open document
            with open("test_good.py", "r") as f:
                text = f.read()
            
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_good.py",
                    "languageId": "python",
                    "version": 1,
                    "text": text
                }
            })
            
            # Give server time to process
            time.sleep(1)
            
            # Test rename if supported
            if capabilities.get('renameProvider'):
                print("\n=== Testing Rename ===")
                rename_response = client.send_request("textDocument/rename", {
                    "textDocument": {
                        "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_good.py"
                    },
                    "position": {"line": 7, "character": 0},  # Position of 'calc'
                    "newName": "calculator"
                })
                
                if rename_response and "result" in rename_response:
                    print("Rename supported! Changes would be:")
                    changes = rename_response["result"].get("changes", {})
                    for uri, edits in changes.items():
                        print(f"  File: {uri}")
                        for edit in edits:
                            print(f"    - Replace at {edit['range']}: '{edit['newText']}'")
                else:
                    print("Rename request failed or returned no results")
            
            # Test references if supported  
            if capabilities.get('referencesProvider'):
                print("\n=== Testing Find References ===")
                refs_response = client.send_request("textDocument/references", {
                    "textDocument": {
                        "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_good.py"
                    },
                    "position": {"line": 7, "character": 0},  # Position of 'calc'
                    "context": {"includeDeclaration": True}
                })
                
                if refs_response and "result" in refs_response:
                    refs = refs_response["result"]
                    print(f"Found {len(refs)} references:")
                    for ref in refs:
                        print(f"  - {ref['uri']} at {ref['range']}")
                else:
                    print("References request failed or returned no results")
                    
        else:
            print("Failed to initialize Pyright LSP")
            
    finally:
        client.stop()

if __name__ == "__main__":
    test_pyright_capabilities()