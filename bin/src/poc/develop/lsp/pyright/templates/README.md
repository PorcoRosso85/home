# Pyright LSP JSON Templates

This directory contains JSON-RPC 2.0 templates for interacting with Pyright Language Server.

## Usage

These templates can be used with the `/entry` command system for LLM-first interaction.

### Template Variables

Each template contains placeholder variables (marked with `${VARIABLE_NAME}`) that should be replaced:

- `${WORKSPACE_PATH}`: Absolute path to your workspace directory
- `${FILE_PATH}`: Absolute path to the Python file
- `${FILE_CONTENT}`: The actual content of the Python file
- `${LINE}`: Line number (0-indexed)
- `${CHARACTER}`: Character position in line (0-indexed)
- `${NEW_NAME}`: New name for rename operations
- `${ACTION_KIND}`: Type of code action (e.g., "quickfix", "source.organizeImports")

### Example Usage

1. **Initialize the server:**
   ```bash
   cat templates/initialize.json | \
   sed "s|\${WORKSPACE_PATH}|/your/workspace/path|g" | \
   pyright-langserver --stdio
   ```

2. **Using with entry system:**
   ```bash
   echo '{
     "type": "template",
     "template": "rename",
     "parameters": {
       "file_path": "/path/to/file.py",
       "line": 10,
       "character": 5,
       "new_name": "better_variable_name"
     }
   }' | nix run .#run
   ```

### Available Templates

1. **initialize.json** - Initialize the LSP server with full capabilities
2. **document_open.json** - Open a document for analysis
3. **rename.json** - Rename a symbol across the codebase
4. **find_references.json** - Find all references to a symbol
5. **goto_definition.json** - Navigate to symbol definition
6. **hover.json** - Get hover information for a symbol
7. **code_action.json** - Request code actions (fixes, refactoring)
8. **completion.json** - Get code completions
9. **document_symbols.json** - List all symbols in a document

### LSP Message Format

All messages follow the LSP specification with Content-Length headers:

```
Content-Length: 146\r\n
\r\n
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}
```

### Notes

- Line and character positions are 0-indexed
- File URIs must use the `file://` scheme
- The server must be initialized before sending other requests
- Some operations require the document to be opened first