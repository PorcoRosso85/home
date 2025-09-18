"""Pyright LSP client for type-aware code analysis."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, TypedDict


class ErrorResult(TypedDict):
    """Error result type."""
    ok: bool
    error: str


class InitializeSuccess(TypedDict):
    """Success result for initialize operation."""
    ok: bool


class SymbolsSuccess(TypedDict):
    """Success result for symbol operations."""
    ok: bool
    symbols: List[Dict[str, Any]]


class PyrightLSPClient:
    """Client for communicating with Pyright Language Server."""
    
    def __init__(self):
        self.is_initialized: bool = False
        self.workspace_path: Optional[Path] = None
        self.proc: Optional[subprocess.Popen] = None
        self._request_id: int = 0
        
    async def initialize(self, workspace_path: str) -> Union[InitializeSuccess, ErrorResult]:
        """Initialize the Pyright LSP server.
        
        Args:
            workspace_path: Path to the workspace directory
            
        Returns:
            InitializeSuccess if successful, ErrorResult if already initialized
        """
        if self.is_initialized:
            return ErrorResult(ok=False, error="Client is already initialized")
            
        self.workspace_path = Path(workspace_path)
        
        # Start LSP server
        # Find pyright-langserver in infrastructure/pyright/
        langserver_path = Path(__file__).parent / "infrastructure" / "pyright" / "pyright-langserver"
        if not langserver_path.exists():
            return ErrorResult(ok=False, error=f"pyright-langserver not found at {langserver_path}")
            
        self.proc = subprocess.Popen(
            [str(langserver_path), "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workspace_path
        )
        
        # Send initialize request
        root_uri = f"file://{os.path.abspath(workspace_path)}"
        await self._send_request("initialize", {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "capabilities": {
                "textDocument": {
                    "documentSymbol": {
                        "hierarchicalDocumentSymbolSupport": True
                    }
                },
                "workspace": {
                    "symbol": {
                        "dynamicRegistration": False
                    }
                }
            }
        })
        
        # Send initialized notification
        await self._send_notification("initialized", {})
        
        self.is_initialized = True
        return InitializeSuccess(ok=True)
        
    async def shutdown(self) -> None:
        """Shutdown the Pyright LSP server."""
        if not self.is_initialized:
            return
            
        if self.proc:
            await self._send_request("shutdown", None)
            await self._send_notification("exit", None)
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            
        self.is_initialized = False
        self.workspace_path = None
        self.proc = None
        
    async def get_document_symbols(self, file_path: str) -> Union[SymbolsSuccess, ErrorResult]:
        """Get symbols from a specific document.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            SymbolsSuccess with list of symbol dictionaries, or ErrorResult if not initialized
        """
        if not self.is_initialized:
            return ErrorResult(ok=False, error="Client not initialized")
            
        # Open the document
        await self._open_document(file_path)
        
        # Request document symbols
        uri = f"file://{os.path.abspath(file_path)}"
        response = await self._send_request("textDocument/documentSymbol", {
            "textDocument": {"uri": uri}
        })
        
        # Parse and format symbols
        symbols = []
        if response and "result" in response:
            raw_symbols = response["result"]
            symbols = self._parse_document_symbols(raw_symbols, uri)
            
        return SymbolsSuccess(ok=True, symbols=symbols)
        
    async def get_workspace_symbols(self, query: str = "") -> Union[SymbolsSuccess, ErrorResult]:
        """Get all symbols in the workspace.
        
        Args:
            query: Optional search query
            
        Returns:
            SymbolsSuccess with list of symbol dictionaries, or ErrorResult if not initialized
        """
        if not self.is_initialized:
            return ErrorResult(ok=False, error="Client not initialized")
            
        # Find all Python files in workspace
        all_symbols = []
        for py_file in self.workspace_path.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):
                result = await self.get_document_symbols(str(py_file))
                if result["ok"]:
                    all_symbols.extend(result["symbols"])
                
        return SymbolsSuccess(ok=True, symbols=all_symbols)
        
    async def _send_request(self, method: str, params: Any) -> Dict[str, Any]:
        """Send a request to the LSP server and wait for response."""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        content = json.dumps(request)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        self.proc.stdin.write((header + content).encode())
        self.proc.stdin.flush()
        
        # Read response
        return await self._read_response()
        
    async def _send_notification(self, method: str, params: Any) -> None:
        """Send a notification to the LSP server (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        content = json.dumps(notification)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        self.proc.stdin.write((header + content).encode())
        self.proc.stdin.flush()
        
    async def _read_response(self) -> Dict[str, Any]:
        """Read a response from the LSP server."""
        # Read headers
        headers = {}
        while True:
            line = self.proc.stdout.readline().decode().strip()
            if not line:
                break
            key, value = line.split(": ", 1)
            headers[key] = value
            
        # Read content
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = self.proc.stdout.read(content_length).decode()
            return json.loads(content)
            
        return {}
        
    async def _open_document(self, file_path: str) -> None:
        """Open a document in the LSP server."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        uri = f"file://{os.path.abspath(file_path)}"
        
        await self._send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": "python",
                "version": 1,
                "text": content
            }
        })
        
    def _parse_document_symbols(self, raw_symbols: List[Any], uri: str) -> List[Dict[str, Any]]:
        """Parse raw document symbols into our format."""
        symbols = []
        
        for symbol in raw_symbols:
            parsed = {
                "name": symbol.get("name", ""),
                "kind": self._get_symbol_kind(symbol.get("kind", 0)),
                "location": {
                    "uri": uri,
                    "range": symbol.get("range", {})
                },
                "type_info": {
                    "signature": symbol.get("detail", "")
                } if symbol.get("detail") else None,
                "is_async": False  # TODO: Detect from detail
            }
            
            symbols.append(parsed)
            
            # Process children recursively
            if "children" in symbol:
                child_symbols = self._parse_document_symbols(symbol["children"], uri)
                symbols.extend(child_symbols)
                
        return symbols
        
    def _get_symbol_kind(self, kind_num: int) -> str:
        """Convert LSP SymbolKind number to string."""
        kinds = {
            1: "file",
            2: "module", 
            3: "namespace",
            4: "package",
            5: "class",
            6: "method",
            7: "property",
            8: "field",
            9: "constructor",
            10: "enum",
            11: "interface",
            12: "function",
            13: "variable",
            14: "constant",
            15: "string",
            16: "number",
            17: "boolean",
            18: "array",
            19: "object",
            20: "key",
            21: "null",
            22: "enum_member",
            23: "struct",
            24: "event",
            25: "operator",
            26: "type_parameter"
        }
        return kinds.get(kind_num, "unknown")