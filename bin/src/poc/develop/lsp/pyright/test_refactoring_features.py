#!/usr/bin/env python3
"""Test all refactoring features in Pyright."""

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

def test_all_refactoring_features():
    """Test all refactoring features."""
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
                    "rename": {"prepareSupport": True},
                    "references": {},
                    "definition": {},
                    "typeDefinition": {},
                    "hover": {},
                    "documentSymbol": {},
                    "codeAction": {
                        "codeActionLiteralSupport": {
                            "codeActionKind": {
                                "valueSet": [
                                    "",
                                    "quickfix",
                                    "refactor",
                                    "refactor.extract",
                                    "refactor.extract.function",
                                    "refactor.extract.method",
                                    "refactor.extract.variable",
                                    "refactor.inline",
                                    "refactor.inline.variable",
                                    "refactor.inline.function",
                                    "refactor.move",
                                    "refactor.rewrite",
                                    "source",
                                    "source.organizeImports",
                                    "source.fixAll"
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        response = client.send_request("initialize", init_params)
        if response and "result" in response:
            capabilities = response["result"]["capabilities"]
            
            print("\n=== Pyright Refactoring Capabilities ===")
            
            # Basic features
            print("\n[Basic Features]")
            print(f"✓ Rename: {bool(capabilities.get('renameProvider'))}")
            print(f"✓ Find References: {bool(capabilities.get('referencesProvider'))}")
            print(f"✓ Go to Definition: {bool(capabilities.get('definitionProvider'))}")
            print(f"✓ Go to Type Definition: {bool(capabilities.get('typeDefinitionProvider'))}")
            
            # Code actions
            code_action_provider = capabilities.get('codeActionProvider', {})
            if isinstance(code_action_provider, dict):
                kinds = code_action_provider.get('codeActionKinds', [])
                print("\n[Code Actions Supported]")
                print(f"✓ Quick Fix: {'quickfix' in kinds}")
                print(f"✓ Organize Imports: {'source.organizeImports' in kinds}")
                
                # Check for refactoring actions
                print("\n[Refactoring Actions]")
                refactor_kinds = [k for k in kinds if k.startswith('refactor')]
                if refactor_kinds:
                    for kind in refactor_kinds:
                        print(f"  - {kind}")
                else:
                    print("  - No specific refactor actions found")
            
            # Additional features
            print("\n[Additional Features]")
            print(f"✓ Document Symbols: {bool(capabilities.get('documentSymbolProvider'))}")
            print(f"✓ Workspace Symbols: {bool(capabilities.get('workspaceSymbolProvider'))}")
            print(f"✓ Call Hierarchy: {bool(capabilities.get('callHierarchyProvider'))}")
            print(f"✓ Semantic Tokens: {bool(capabilities.get('semanticTokensProvider'))}")
            
            # Send initialized notification
            client.send_notification("initialized")
            
            # Test extract function/variable
            test_code = '''def process_data(data):
    # This could be extracted as a function
    total = 0
    for item in data:
        if item > 0:
            total += item * 2
        else:
            total += item
    
    # This could be extracted as a variable
    result = total * 1.1 + 100
    
    return result
'''
            
            # Open document
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_extract.py",
                    "languageId": "python",
                    "version": 1,
                    "text": test_code
                }
            })
            
            # Give server time to process
            time.sleep(1)
            
            # Test code actions for potential extraction
            print("\n=== Testing Extract Refactoring ===")
            extract_response = client.send_request("textDocument/codeAction", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_extract.py"
                },
                "range": {
                    "start": {"line": 2, "character": 4},
                    "end": {"line": 7, "character": 25}
                },
                "context": {
                    "only": ["refactor.extract", "refactor.extract.function", "refactor.extract.method"]
                }
            })
            
            if extract_response and "result" in extract_response:
                actions = extract_response["result"]
                print(f"Extract actions available: {len(actions)}")
                for action in actions:
                    print(f"- {action.get('title', 'Untitled')}")
            else:
                print("No extract refactoring actions available")
                
            # Test prepare rename
            print("\n=== Testing Prepare Rename ===")
            prepare_rename_response = client.send_request("textDocument/prepareRename", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_extract.py"
                },
                "position": {"line": 2, "character": 4}  # Position of 'total'
            })
            
            if prepare_rename_response and "result" in prepare_rename_response:
                print(f"Can rename at position: {prepare_rename_response['result']}")
            else:
                print("Cannot prepare rename at this position")
                
        else:
            print("Failed to initialize Pyright LSP")
            
    finally:
        client.stop()

if __name__ == "__main__":
    test_all_refactoring_features()