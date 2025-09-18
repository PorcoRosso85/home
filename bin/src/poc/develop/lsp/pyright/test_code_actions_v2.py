#!/usr/bin/env python3
"""Test Pyright LSP Code Actions with diagnostics."""

import json
import subprocess
import time
from threading import Thread
import queue

class LSPClient:
    def __init__(self):
        self.proc = None
        self.response_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        self.request_id = 0
        self.diagnostics = []
        
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
                    
                    # Handle diagnostics
                    if response.get("method") == "textDocument/publishDiagnostics":
                        self.diagnostics = response["params"]["diagnostics"]
                        self.notification_queue.put(response)
                    elif "id" in response:
                        self.response_queue.put(response)
                    else:
                        self.notification_queue.put(response)
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
    
    def wait_for_diagnostics(self, timeout=3):
        """Wait for diagnostics to arrive."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.notification_queue.get(timeout=0.1)
            except queue.Empty:
                pass
            if self.diagnostics:
                return True
        return False
    
    def stop(self):
        """Stop the server."""
        if self.proc:
            self.send_request("shutdown")
            self.send_notification("exit")
            self.proc.terminate()
            self.proc.wait()

def test_code_actions():
    """Test Pyright's code action capabilities."""
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
                    "codeAction": {
                        "codeActionLiteralSupport": {
                            "codeActionKind": {
                                "valueSet": [
                                    "",
                                    "quickfix",
                                    "refactor",
                                    "refactor.extract",
                                    "refactor.inline",
                                    "refactor.rewrite",
                                    "source",
                                    "source.organizeImports",
                                    "source.fixAll"
                                ]
                            }
                        }
                    },
                    "publishDiagnostics": {
                        "relatedInformation": True,
                        "versionSupport": False,
                        "codeDescriptionSupport": True,
                        "dataSupport": True
                    }
                },
                "workspace": {
                    "workspaceFolders": True
                }
            },
            "workspaceFolders": [{
                "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright",
                "name": "pyright-test"
            }]
        }
        
        response = client.send_request("initialize", init_params)
        if response and "result" in response:
            capabilities = response["result"]["capabilities"]
            print(f"\nCode Action Provider: {capabilities.get('codeActionProvider', False)}")
            
            # Send initialized notification
            client.send_notification("initialized")
            
            # Create test file with issues
            test_code = '''import os
import sys
import json
import os  # duplicate import

def calculate(x: int, y: int) -> int:
    z = x + y  # unused variable
    return x + y

# Missing type hints
def greet(name):
    return f"Hello, {name}"

# Undefined name error
result = undefined_function()

# Type error
number: int = "not a number"
'''
            
            # Save test file
            with open("test_actions.py", "w") as f:
                f.write(test_code)
            
            # Open document
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py",
                    "languageId": "python",
                    "version": 1,
                    "text": test_code
                }
            })
            
            # Wait for diagnostics
            print("\n=== Waiting for Diagnostics ===")
            if client.wait_for_diagnostics():
                print(f"Received {len(client.diagnostics)} diagnostics:")
                for diag in client.diagnostics:
                    print(f"- {diag['message']} at line {diag['range']['start']['line'] + 1}")
            
            # Request code actions with diagnostics
            print("\n=== Requesting Code Actions ===")
            
            # Test 1: Code actions for a specific diagnostic (undefined function)
            if client.diagnostics:
                # Find the undefined function diagnostic
                undefined_diag = None
                for diag in client.diagnostics:
                    if "undefined" in diag['message'].lower():
                        undefined_diag = diag
                        break
                
                if undefined_diag:
                    print(f"\nCode actions for: {undefined_diag['message']}")
                    code_actions_response = client.send_request("textDocument/codeAction", {
                        "textDocument": {
                            "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py"
                        },
                        "range": undefined_diag['range'],
                        "context": {
                            "diagnostics": [undefined_diag]
                        }
                    })
                    
                    if code_actions_response and "result" in code_actions_response:
                        actions = code_actions_response["result"]
                        print(f"Found {len(actions)} code actions:")
                        for action in actions:
                            print(f"- {action.get('title', 'Untitled')}")
            
            # Test 2: Organize imports
            print("\n=== Testing Organize Imports ===")
            organize_response = client.send_request("textDocument/codeAction", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py"
                },
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 18, "character": 0}
                },
                "context": {
                    "only": ["source.organizeImports"],
                    "diagnostics": []
                }
            })
            
            if organize_response and "result" in organize_response:
                organize_actions = organize_response["result"]
                print(f"Found {len(organize_actions)} organize import actions")
                for action in organize_actions:
                    print(f"- {action.get('title', 'Untitled')}")
                    if 'edit' in action and 'changes' in action['edit']:
                        print("  Changes:")
                        for uri, edits in action['edit']['changes'].items():
                            for edit in edits:
                                print(f"    {edit}")
                    
        else:
            print("Failed to initialize Pyright LSP")
            
    finally:
        # Clean up test file
        import os
        if os.path.exists("test_actions.py"):
            os.remove("test_actions.py")
        client.stop()

if __name__ == "__main__":
    test_code_actions()