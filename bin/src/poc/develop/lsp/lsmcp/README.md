# LSMCP Wrapper - No Clone Required

LSP client wrapper using LSMCP's approach without local cloning. Manages dependencies via Nix flakes.

## Prerequisites
- Nix 2.4+ with flakes enabled
- Language servers auto-provided by Nix

## Quick Start

```bash
# Test all features
nix run .#test-lsp-features

# Find references
nix run .#lsp-python -- 'console.log(await findReferences("file.py", 10, "symbol"))'

# Get definition  
nix run .#lsp-typescript -- 'console.log(await getDefinition("file.ts", 20, "function"))'
```

## Available Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `findReferences(file, line, symbol?)` | Find all usages | Returns `[{file, line, column}, ...]` |
| `getDefinition(file, line, symbol?)` | Jump to definition | Returns definition location |
| `getDocumentSymbols(file)` | List all symbols | Returns symbols with kinds |
| `hover(file, line, column?)` | Get type info | Returns type/docs string |

## Architecture

- **Nix flake**: References LSMCP at specific commit (no clone needed)
- **cli.ts**: LSP client implementation  
- **Language runners**: Wrapped commands for each language

## How It Works

1. Nix fetches LSMCP from GitHub to `/nix/store/`
2. cli.ts spawns language server and handles LSP protocol
3. Results returned as JSON

## Real Example

```bash
# Create test file
cat > example.py << 'EOF'
def process(data):
    return data.upper()

result = process("hello")
print(result)
EOF

# Find all references to 'process'
nix run .#lsp-python -- '
  const refs = await findReferences("example.py", 1, "process");
  console.log(`Found ${refs.length} references`);
  refs.forEach(r => console.log(`  Line ${r.line}`));
'
```

## Updating LSMCP

```nix
# In flake.nix, change:
url = "github:mizchi/lsmcp/<new-commit-hash>";

# Then:
nix flake update
```

## Adding Languages

1. Edit `flake.nix`:
```nix
lsp-go = mkLspRunner {
  name = "lsp-go";
  lspCmd = "${pkgs.gopls}/bin";
};
```

2. Edit `cli.ts` to handle `.go` extension

## Troubleshooting

- **Timeout**: Increase timeout in cli.ts
- **No results**: Check file path and line numbers
- **Errors**: Enable debug with `DEBUG=1`

## Benefits

✅ No manual clone  
✅ Version pinning  
✅ Reproducible  
✅ Clean project  

## Limitations

- Read-only operations
- Single file context
- Language server dependent features