# ASVS Reference Arrow Converter

A lightweight tool for converting OWASP ASVS (Application Security Verification Standard) data directly from the official GitHub repository to Apache Arrow/Parquet format.

## Primary Input

**Input Source**: `github:OWASP/ASVS`
- Automatically fetched via Nix flakes from the official repository
- No manual cloning or downloading required
- Always uses the latest official ASVS markdown files
- Defined in `flake.nix`:
  ```nix
  asvs-source = {
    url = "github:OWASP/ASVS";
    flake = false;
  };
  ```

## Purpose

This tool provides a direct pipeline from GitHub to Arrow format:
- **GitHub → Arrow**: Convert ASVS markdown files to columnar format
- **Zero Manual Steps**: Nix handles fetching and conversion
- **Type-Safe**: Strongly typed Arrow schemas
- **Efficient Storage**: Output as compressed Parquet files
- **Analysis Ready**: Compatible with pandas, DuckDB, Polars, etc.

## Architecture

### Data Flow
```
github:OWASP/ASVS → Nix Flake → Markdown Parser → Arrow Table → Parquet File
```

### Components
```
asvs_reference/
├── flake.nix               # Fetches ASVS from GitHub
├── asvs_arrow_converter.py # Markdown to Arrow conversion
├── asvs_arrow_types.py     # Arrow schema definitions
├── arrow_cli.py            # CLI for conversion
└── test_arrow_converter.py # Tests
```

## Usage

### Quick Start with Nix (Recommended)

```bash
# Convert ASVS 5.0 from GitHub to Parquet in one command
nix run .#convert-example

# Output: output/asvs_v5.0.parquet (345 requirements, ~50KB)
```

This single command:
1. Fetches ASVS from `github:OWASP/ASVS`
2. Parses all V*.md files
3. Converts to Arrow format
4. Saves as compressed Parquet

### CLI Usage

```bash
# If you need custom options
nix run .#arrow-cli -- ${ASVS_SOURCE_PATH}/5.0 -o custom.parquet -c gzip

# Available compressions: snappy (default), gzip, brotli, lz4, zstd
```

### Python API

```python
from asvs_arrow_converter import ASVSArrowConverter

# The converter expects a path to ASVS markdown directory
# In Nix, this is automatically provided from GitHub
converter = ASVSArrowConverter("/path/to/asvs/5.0")

# Get Arrow table
table = converter.get_requirements_table()
print(f"Requirements: {table.num_rows}")
print(f"Schema: {table.schema}")

# Save as Parquet
converter.to_parquet("asvs.parquet")
```

### Reading Output

```python
import pyarrow.parquet as pq

# Read Parquet file
table = pq.read_table("output/asvs_v5.0.parquet")

# Analyze with pandas
df = table.to_pandas()
print(f"Total: {len(df)} requirements")
print(f"Level 1: {df['level1'].sum()} requirements")

# Or use with DuckDB
import duckdb
duckdb.sql("SELECT * FROM 'output/asvs_v5.0.parquet' WHERE level1 = true")
```

## Arrow Schema

The output Arrow table has the following schema:

| Column | Type | Description |
|--------|------|-------------|
| uri | string | Unique identifier (e.g., "asvs:5.0:req:2.1.1") |
| number | string | Requirement number (e.g., "2.1.1") |
| description | string | Full requirement text |
| level1 | bool | Required for Level 1 |
| level2 | bool | Required for Level 2 |
| level3 | bool | Required for Level 3 |
| section | string | Section name |
| chapter | string | Chapter name |
| tags | list<string> | Optional tags |
| cwe | list<int32> | CWE IDs mentioned |
| nist | list<string> | NIST references |

## Dependencies

- **Runtime**: PyArrow only
- **Build**: Nix (for GitHub fetching)
- **Optional**: pandas (for DataFrame conversion)

## Development

```bash
# Enter development shell
nix develop

# Run tests
pytest test_arrow_converter.py -v

# Run CLI directly
./arrow_cli.py --help
```

## Key Benefits

1. **Authoritative Source**: Always uses official OWASP/ASVS from GitHub
2. **No Manual Steps**: Nix automates fetching and setup
3. **Minimal Dependencies**: Only PyArrow required
4. **Fast**: Arrow columnar format for efficient processing
5. **Portable**: Parquet files work across languages and tools

## License

Same as OWASP ASVS project.