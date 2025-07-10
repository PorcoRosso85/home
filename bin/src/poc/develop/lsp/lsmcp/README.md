# LSMCP Wrapper - No Clone Required

This implementation demonstrates using LSMCP's approach without cloning the repository locally.

## Architecture

- **External repository**: LSMCP is referenced via Nix flake input
- **Local wrapper**: `cli.ts` implements the LSP client logic
- **Nix packaging**: Each language gets its own command

## Key Achievement

**No local clone needed!** LSMCP source is fetched by Nix and stored in `/nix/store/`.

## Usage

```bash
# Test all features
nix run .#test-lsp-features

# Use individual language servers
nix run .#lsp-python -- 'await findReferences("file.py", 10, "variable")'
nix run .#lsp-typescript -- 'await getDefinition("file.ts", 20, "function")'
```

## Verified Features

All tested with pyright-langserver:

| Feature | Status | Example Result |
|---------|--------|----------------|
| findReferences | ✅ | Found 2 references |
| getDefinition | ✅ | Found definition at line 5 |
| getDocumentSymbols | ✅ | Found 8 symbols |
| hover | ✅ | Shows type info |

## How It Works

1. **Nix flake input** references LSMCP at specific commit:
   ```nix
   lsmcp-src = {
     url = "github:mizchi/lsmcp/35da2b193b0fc1326ba6bebcff62fcf0cbeac1b5";
     flake = false;
   };
   ```

2. **cli.ts** implements LSP client (based on LSMCP's approach)

3. **Nix wraps** everything into executable commands

## Benefits

- **Version control**: Specific commit in flake.nix
- **No manual clone**: Nix handles downloading
- **Clean project**: No external repos in your tree
- **Reproducible**: Same version everywhere

## Updating LSMCP Version

Edit `flake.nix` and change the commit hash:
```nix
url = "github:mizchi/lsmcp/<new-commit-hash>";
```

Then run `nix flake update`.