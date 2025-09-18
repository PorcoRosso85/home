#!/usr/bin/env python3
"""Direct test of Pyright LSP refactoring capabilities."""

import json
import subprocess
import sys
from pathlib import Path

def send_request(proc, request):
    """Send LSP request and get response."""
    request_str = json.dumps(request)
    content_length = len(request_str.encode('utf-8'))
    header = f"Content-Length: {content_length}\r\n\r\n"
    message = header + request_str
    
    proc.stdin.write(message.encode('utf-8'))
    proc.stdin.flush()
    
    # Read response header
    headers = {}
    while True:
        line = proc.stdout.readline().decode('utf-8').strip()
        if not line:
            break
        key, value = line.split(': ')
        headers[key] = value
    
    # Read response body
    content_length = int(headers.get('Content-Length', '0'))
    response = proc.stdout.read(content_length).decode('utf-8')
    return json.loads(response)

def test_pyright_refactoring():
    """Test Pyright's refactoring capabilities."""
    test_file = Path(__file__).parent / "test_good.py"
    test_uri = f"file://{test_file.absolute()}"
    
    # Start pyright-langserver
    proc = subprocess.Popen(
        ["pyright-langserver", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootPath": str(Path.cwd()),
                "rootUri": f"file://{Path.cwd()}",
                "capabilities": {
                    "textDocument": {
                        "rename": {"prepareSupport": True},
                        "references": {}
                    }
                }
            }
        }
        
        response = send_request(proc, init_request)
        print("Initialize response:", json.dumps(response, indent=2))
        
        # Check capabilities
        if "result" in response and "capabilities" in response["result"]:
            caps = response["result"]["capabilities"]
            print("\nServer capabilities:")
            print(f"- Rename provider: {caps.get('renameProvider', False)}")
            print(f"- References provider: {caps.get('referencesProvider', False)}")
            
            # Open document
            open_request = {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": test_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": test_file.read_text()
                    }
                }
            }
            send_request(proc, open_request)
            
            # Test rename if supported
            if caps.get('renameProvider'):
                print("\nTesting rename...")
                rename_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "textDocument/rename",
                    "params": {
                        "textDocument": {"uri": test_uri},
                        "position": {"line": 7, "character": 7},  # Position of 'calc'
                        "newName": "calculator"
                    }
                }
                rename_response = send_request(proc, rename_request)
                print("Rename response:", json.dumps(rename_response, indent=2))
            
            # Test references if supported
            if caps.get('referencesProvider'):
                print("\nTesting references...")
                refs_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "textDocument/references",
                    "params": {
                        "textDocument": {"uri": test_uri},
                        "position": {"line": 7, "character": 7},  # Position of 'calc'
                        "context": {"includeDeclaration": True}
                    }
                }
                refs_response = send_request(proc, refs_request)
                print("References response:", json.dumps(refs_response, indent=2))
        
    finally:
        # Shutdown
        shutdown_request = {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "shutdown"
        }
        send_request(proc, shutdown_request)
        
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_pyright_refactoring()