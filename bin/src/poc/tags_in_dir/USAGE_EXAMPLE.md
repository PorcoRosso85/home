# Usage Example for tags_in_dir Library

This directory provides a Nix flake library for ctags-based code analysis with KuzuDB persistence.

## Using as a Library in Another Flake

### 1. Add to Your Flake Inputs

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    tags-in-dir.url = "path:/home/nixos/bin/src/poc/tags_in_dir";
    # Or from git:
    # tags-in-dir.url = "github:yourusername/tags-in-dir";
  };

  outputs = { self, nixpkgs, flake-utils, tags-in-dir }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Method 1: Use the overlay
        pkgsWithTags = import nixpkgs {
          inherit system;
          overlays = [ tags-in-dir.overlays.${system}.default ];
        };
        
        # Method 2: Use the package directly
        tagsInDirPkg = tags-in-dir.packages.${system}.default;
        
        # Create Python environment with tags-in-dir
        pythonEnv = pkgs.python3.withPackages (ps: [
          tagsInDirPkg
          # Add other dependencies
          ps.pandas
          ps.matplotlib
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.universal-ctags  # Required for ctags functionality
          ];
        };
        
        # Your applications here
        apps.analyze = {
          type = "app";
          program = "${pkgs.writeScript "analyze" ''
            #!${pythonEnv}/bin/python
            from tags_in_dir import CtagsParser, Symbol
            from tags_in_dir.kuzu_storage import KuzuStorage
            from tags_in_dir.call_detector import CallDetector
            
            # Your analysis code here
            parser = CtagsParser()
            symbols = parser.extract_symbols(".")
            
            # Store in KuzuDB
            storage = KuzuStorage("analysis.db")
            storage.store_symbols(symbols)
            
            print(f"Analyzed {len(symbols)} symbols")
          ''}";
        };
      });
}
```

## Using in Python Code

### Basic Usage

```python
from tags_in_dir import CtagsParser, Symbol
from tags_in_dir.kuzu_storage import KuzuStorage
from tags_in_dir.call_detector import CallDetector

# Parse symbols from a directory
parser = CtagsParser()
symbols = parser.extract_symbols("/path/to/project", extensions=[".py", ".js"])

# Store in KuzuDB
storage = KuzuStorage("project_analysis.db")
stored_count = storage.store_symbols(symbols)

# Detect function calls
detector = CallDetector(symbols)
relationships = detector.detect_all_calls("/path/to/project")

# Resolve and store call relationships
resolved_calls = detector.resolve_call_targets(relationships)
for from_uri, to_uri, line_no in resolved_calls:
    storage.create_calls_relationship(from_uri, to_uri, line_no)

# Query the results
stats = storage.get_statistics()
print(f"Total symbols: {stats['total_symbols']}")
print(f"Total call relationships: {stats['total_relationships']}")
```

### Advanced Queries

```python
# Find all functions in a specific file
symbols_in_file = storage.find_symbols_by_file("main.py")

# Find all occurrences of a function
function_refs = storage.find_symbols_by_name("process_data")

# Find call graph for a function
location_uri = "file:///home/user/project/main.py#L42"
called_by, calling = storage.find_symbol_calls(location_uri)

# Custom Cypher queries
results = storage.execute_cypher("""
    MATCH (f:Symbol {kind: 'function'})-[:CALLS]->(g:Symbol {kind: 'function'})
    WHERE f.name CONTAINS 'test_'
    RETURN f.name, g.name, COUNT(*) as call_count
    ORDER BY call_count DESC
""")
```

## Available Outputs

This flake provides several outputs:

### Packages
- `packages.default` - The Python package itself
- `packages.cli` - Command-line interface wrapper
- `packages.pythonEnv` - Python environment with the library pre-installed

### Overlay
- `overlays.default` - Adds `tags-in-dir` to `pythonPackagesExtensions`

### Library Functions
- `lib.mkPythonEnvWith` - Helper to create Python environment with tags-in-dir and additional packages

## Direct CLI Usage

```bash
# Run the CLI directly
nix run path:/home/nixos/bin/src/poc/tags_in_dir#cli -- /path/to/analyze

# Run tests
nix run path:/home/nixos/bin/src/poc/tags_in_dir#test

# See all available commands
nix run path:/home/nixos/bin/src/poc/tags_in_dir
```

## Development

```bash
# Enter development shell
nix develop path:/home/nixos/bin/src/poc/tags_in_dir

# The library is available in Python
python -c "from tags_in_dir import CtagsParser; print(CtagsParser)"
```