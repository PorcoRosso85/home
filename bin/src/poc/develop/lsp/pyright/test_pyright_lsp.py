#!/usr/bin/env python3
"""Pytest suite for Pyright LSP functionality."""

import json
import subprocess
import time
import pytest
from threading import Thread
import queue
from pathlib import Path
import tempfile
import shutil


class PyrightLSPClient:
    """Pyright LSP client for testing."""
    
    def __init__(self):
        self.proc = None
        self.response_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        self.request_id = 0
        self.is_running = False
        
    def start(self):
        """Start pyright-langserver process."""
        self.proc = subprocess.Popen(
            ["pyright-langserver", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.is_running = True
        
        # Start reader thread
        reader_thread = Thread(target=self._read_responses)
        reader_thread.daemon = True
        reader_thread.start()
        
    def _read_responses(self):
        """Read responses from stdout."""
        while self.is_running:
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
                    
                    if "id" in response:
                        self.response_queue.put(response)
                    else:
                        self.notification_queue.put(response)
            except Exception:
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
        if self.proc and self.is_running:
            self.is_running = False
            self.send_request("shutdown")
            self.send_notification("exit")
            self.proc.terminate()
            self.proc.wait()


@pytest.fixture
def lsp_client():
    """Create and manage LSP client."""
    client = PyrightLSPClient()
    client.start()
    yield client
    client.stop()


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for tests."""
    workspace = tempfile.mkdtemp()
    yield workspace
    shutil.rmtree(workspace)


@pytest.fixture
def initialized_client(lsp_client, temp_workspace):
    """Initialize LSP client with workspace."""
    response = lsp_client.send_request("initialize", {
        "processId": None,
        "rootPath": temp_workspace,
        "rootUri": f"file://{temp_workspace}",
        "capabilities": {
            "textDocument": {
                "rename": {"prepareSupport": True},
                "references": {},
                "definition": {},
                "codeAction": {
                    "codeActionLiteralSupport": {
                        "codeActionKind": {
                            "valueSet": ["quickfix", "source.organizeImports"]
                        }
                    }
                }
            }
        }
    })
    
    assert response is not None
    assert "result" in response
    
    lsp_client.send_notification("initialized")
    
    yield lsp_client, temp_workspace, response["result"]["capabilities"]


class TestPyrightCapabilities:
    """Test Pyright LSP capabilities."""
    
    def test_server_initialization(self, lsp_client, temp_workspace):
        """Test server can be initialized."""
        response = lsp_client.send_request("initialize", {
            "processId": None,
            "rootPath": temp_workspace,
            "rootUri": f"file://{temp_workspace}",
            "capabilities": {}
        })
        
        assert response is not None
        assert response.get("result") is not None
        assert "capabilities" in response["result"]
    
    def test_capabilities_reported(self, initialized_client):
        """Test that server reports expected capabilities."""
        _, _, capabilities = initialized_client
        
        # Basic capabilities
        assert capabilities.get("renameProvider") is not False
        assert capabilities.get("referencesProvider") is not False
        assert capabilities.get("definitionProvider") is not False
        assert capabilities.get("hoverProvider") is not False
        
        # Code action capabilities
        code_action = capabilities.get("codeActionProvider")
        assert code_action is not False
        if isinstance(code_action, dict):
            kinds = code_action.get("codeActionKinds", [])
            assert "quickfix" in kinds
            assert "source.organizeImports" in kinds


class TestRenameRefactoring:
    """Test rename refactoring functionality."""
    
    def test_simple_rename(self, initialized_client):
        """Test renaming a simple variable."""
        client, workspace, _ = initialized_client
        
        # Create test file
        test_file = Path(workspace) / "test_rename.py"
        test_content = """def greet(name):
    message = f"Hello, {name}"
    return message
"""
        test_file.write_text(test_content)
        
        # Open document
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{test_file}",
                "languageId": "python",
                "version": 1,
                "text": test_content
            }
        })
        
        time.sleep(0.5)  # Give server time to process
        
        # Test rename
        response = client.send_request("textDocument/rename", {
            "textDocument": {"uri": f"file://{test_file}"},
            "position": {"line": 1, "character": 4},  # Position of 'message'
            "newName": "greeting"
        })
        
        assert response is not None
        assert "result" in response
        
        # Check if rename edits are provided
        result = response["result"]
        assert "changes" in result or "documentChanges" in result
    
    def test_prepare_rename(self, initialized_client):
        """Test prepare rename functionality."""
        client, workspace, _ = initialized_client
        
        # Create test file
        test_file = Path(workspace) / "test_prepare.py"
        test_content = """count = 0
count += 1
print(count)
"""
        test_file.write_text(test_content)
        
        # Open document
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{test_file}",
                "languageId": "python",
                "version": 1,
                "text": test_content
            }
        })
        
        time.sleep(0.5)
        
        # Test prepare rename
        response = client.send_request("textDocument/prepareRename", {
            "textDocument": {"uri": f"file://{test_file}"},
            "position": {"line": 0, "character": 0}  # Position of 'count'
        })
        
        assert response is not None
        assert "result" in response
        
        # Result should be a range or placeholder
        result = response["result"]
        assert result is not None


class TestFindReferences:
    """Test find references functionality."""
    
    def test_find_all_references(self, initialized_client):
        """Test finding all references to a symbol."""
        client, workspace, _ = initialized_client
        
        # Create test file
        test_file = Path(workspace) / "test_refs.py"
        test_content = """class Calculator:
    def add(self, a, b):
        return a + b

calc = Calculator()
result = calc.add(1, 2)
print(calc)
"""
        test_file.write_text(test_content)
        
        # Open document
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{test_file}",
                "languageId": "python",
                "version": 1,
                "text": test_content
            }
        })
        
        time.sleep(0.5)
        
        # Find references to 'calc'
        response = client.send_request("textDocument/references", {
            "textDocument": {"uri": f"file://{test_file}"},
            "position": {"line": 4, "character": 0},  # Position of 'calc'
            "context": {"includeDeclaration": True}
        })
        
        assert response is not None
        assert "result" in response
        
        references = response["result"]
        assert isinstance(references, list)
        assert len(references) >= 2  # At least definition and one usage


class TestGoToDefinition:
    """Test go to definition functionality."""
    
    def test_go_to_function_definition(self, initialized_client):
        """Test going to function definition."""
        client, workspace, _ = initialized_client
        
        # Create test file
        test_file = Path(workspace) / "test_def.py"
        test_content = """def helper():
    return 42

result = helper()
"""
        test_file.write_text(test_content)
        
        # Open document
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{test_file}",
                "languageId": "python",
                "version": 1,
                "text": test_content
            }
        })
        
        time.sleep(0.5)
        
        # Go to definition
        response = client.send_request("textDocument/definition", {
            "textDocument": {"uri": f"file://{test_file}"},
            "position": {"line": 3, "character": 9}  # Position of 'helper' call
        })
        
        assert response is not None
        assert "result" in response
        
        result = response["result"]
        assert result is not None
        
        # Result can be Location or Location[]
        if isinstance(result, list):
            assert len(result) > 0
            location = result[0]
        else:
            location = result
        
        assert "range" in location
        assert location["range"]["start"]["line"] == 0  # Definition is at line 0


class TestCodeActions:
    """Test code action functionality."""
    
    def test_organize_imports(self, initialized_client):
        """Test organize imports code action."""
        client, workspace, _ = initialized_client
        
        # Create test file with unorganized imports
        test_file = Path(workspace) / "test_imports.py"
        test_content = """import os
import sys
import json
import os  # duplicate

def main():
    pass
"""
        test_file.write_text(test_content)
        
        # Open document
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{test_file}",
                "languageId": "python",
                "version": 1,
                "text": test_content
            }
        })
        
        time.sleep(0.5)
        
        # Request code actions
        response = client.send_request("textDocument/codeAction", {
            "textDocument": {"uri": f"file://{test_file}"},
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 6, "character": 0}
            },
            "context": {
                "only": ["source.organizeImports"]
            }
        })
        
        assert response is not None
        assert "result" in response
        
        # Note: Pyright might not provide organize imports action
        # This test documents the current behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])