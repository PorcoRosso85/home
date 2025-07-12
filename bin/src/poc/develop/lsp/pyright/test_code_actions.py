#!/usr/bin/env python3
"""Test Pyright LSP Code Actions functionality."""

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
                                "valueSet": ["quickfix", "source.organizeImports"]
                            }
                        }
                    }
                }
            }
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

def calculate(x, y):
    z = x + y  # unused variable
    return x + y

# Missing type hints
def greet(name):
    return f"Hello, {name}"

# Undefined name error
result = undefined_function()
'''
            
            # Open document
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py",
                    "languageId": "python",
                    "version": 1,
                    "text": test_code
                }
            })
            
            # Give server time to process
            time.sleep(2)
            
            # Request code actions for the whole document
            print("\n=== Requesting Code Actions ===")
            code_actions_response = client.send_request("textDocument/codeAction", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py"
                },
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 15, "character": 0}
                },
                "context": {
                    "diagnostics": []  # Server will provide its own diagnostics
                }
            })
            
            if code_actions_response and "result" in code_actions_response:
                actions = code_actions_response["result"]
                print(f"\nFound {len(actions)} code actions:")
                for i, action in enumerate(actions):
                    print(f"\n{i+1}. {action.get('title', 'Untitled action')}")
                    if 'kind' in action:
                        print(f"   Kind: {action['kind']}")
                    if 'command' in action:
                        print(f"   Command: {action['command'].get('command', 'N/A')}")
                    if 'edit' in action:
                        print(f"   Has edit: Yes")
                        if 'changes' in action['edit']:
                            for uri, edits in action['edit']['changes'].items():
                                print(f"   Changes in: {uri}")
                                for edit in edits[:2]:  # Show first 2 edits
                                    print(f"     - {edit}")
            else:
                print("No code actions returned or request failed")
                
            # Try specific code action: organize imports
            print("\n=== Testing Organize Imports ===")
            organize_response = client.send_request("textDocument/codeAction", {
                "textDocument": {
                    "uri": "file:///home/nixos/bin/src/poc/develop/lsp/pyright/test_actions.py"
                },
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 3, "character": 0}
                },
                "context": {
                    "only": ["source.organizeImports"]
                }
            })
            
            if organize_response and "result" in organize_response:
                organize_actions = organize_response["result"]
                print(f"Found {len(organize_actions)} organize import actions")
                for action in organize_actions:
                    print(f"- {action.get('title', 'Untitled')}")
                    
        else:
            print("Failed to initialize Pyright LSP")
            
    finally:
        client.stop()

if __name__ == "__main__":
    test_code_actions()