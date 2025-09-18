# Search README

A minimal, strict README-filtered code search tool built on the ck (clueless-skywatcher) backend with a focus on reliability and automation.

## Overview

This tool implements a **strict two-stage search pipeline** for monorepo environments:
1. **Stage1**: Extract directories containing README files that match responsibility descriptions
2. **Stage2**: Search code files only within the filtered directories from Stage1

The implementation prioritizes **clear exit codes** and **strict failure policies** for reliable automation and CI/CD integration.

## Strict Policy (No Fallback)

This tool follows a strict exit policy:
- Pipeline mode fails immediately if no results at any stage
- Clear exit codes for automation and debugging  
- No ambiguous "partial success" states
- Designed for CI/CD environments requiring predictable behavior

## Quick Start

### Prerequisites

- Nix with flakes enabled
- `experimental-features = nix-command flakes` in your Nix configuration

### Basic Usage

```bash
# Two-stage responsibility → code search
nix run . -- -m pipeline "database abstraction"

# JSON output for automation
nix run . -- -m pipeline -f json "authentication"

# README-only search
nix run . -- --scope readme "web framework"

# Traditional search with fallback behavior
nix run . -- "search term"

# Show help and exit codes
nix run . -- --help
```

## Modes

### Pipeline Mode (Default)
Strict two-stage search with no fallbacks:

```bash
# Basic pipeline search
nix run . -- -m pipeline "database"

# JSON output for automation  
nix run . -- -m pipeline -f json "user authentication"
```

**Pipeline Process:**
1. **Stage1**: Search `readme.nix` files for responsibility matches using ck
2. **Stage2**: Search code files only in directories from Stage1
3. **Fail immediately** if either stage returns zero results

### Legacy Mode
Traditional search with fallback behavior:

```bash
# Search all files with fallback
nix run . -- "function definition"

# Search only README files
nix run . -- --scope readme "responsibility"

# Search only code files  
nix run . -- --scope code "error handling"
```

## Output Formats

### Text Format (Default)
Human-readable output with stage summaries:

```
Pipeline Search Results:
========================
Query: database abstraction

Stage1 - README Candidates (2 found):
- ./project-a
- ./project-b

Stage2 - Code Matches (5 found):
- ./project-a/src/db.rs:15: pub struct Database {
- ./project-b/lib/abstract.js:8: class AbstractDB {
...

Total matches: 5
```

### JSON Format
Structured output for automation:

```json
{
  "pipeline": {
    "stage1": {
      "candidates": ["./project-a", "./project-b"],
      "count": 2
    },
    "stage2": {
      "results": [
        {
          "file": "./project-a/src/db.rs",
          "line": 15,
          "content": "pub struct Database {"
        }
      ],
      "count": 5
    }
  },
  "summary": {
    "query": "database abstraction",
    "total_matches": 5
  }
}
```

## Exit Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | Success | Results found and returned |
| 64 | Usage Error | Invalid arguments (EX_USAGE equivalent) |
| 80 | No README Candidates | Stage1 returned zero results |
| 81 | No Code Results | Stage2 returned zero results |
| 101 | ck Not Found | ck command not available in PATH |
| 102 | README Index Error | flake-readme integration failure |

### Pipeline Mode Success Criteria

Pipeline mode success requires:
- **Stage1**: README candidates ≥ 1 (exit 80 if none)
- **Stage2**: Code results ≥ 1 (exit 81 if none)
- **Complete JSON**: `{"pipeline": {"stage1": {...}, "stage2": {...}}}`

## Command Line Interface

```
USAGE:
  search-readme [OPTIONS] QUERY

OPTIONS:
  --scope <SCOPE>     Search scope: readme|code|all (default: all)
  -m <MODE>          Mode: legacy|pipeline (default: legacy)
  -f json, --json    Output format: JSON instead of text
  --help, -h         Show this help message
```

### Option Details

- **`--scope`**: Limit search to specific file types
  - `readme`: Search only README.md and readme.nix files
  - `code`: Search only code files (excludes README files)
  - `all`: Search all file types (default, legacy mode only)

- **`-m`**: Set search mode
  - `legacy`: Traditional search with fallback behavior (default)
  - `pipeline`: Strict two-stage search with immediate failure

- **`-f json` / `--json`**: Output structured JSON instead of human-readable text

## Implementation Details

### Current Packages

- **minimal-ck-wrapper**: Main search tool with strict exit code policy
- **test-harness**: Comprehensive test suite with format and exit code validation
- **format-tests**: JSON/text output format verification
- **exit-code-tests**: Exit code behavior validation

### Technical Architecture

- **ck Backend**: Uses ck (clueless-skywatcher) for semantic search capabilities
- **flake-readme Integration**: Leverages flake-readme for structured README parsing
- **File Discovery**: Uses `find . -name "readme.nix"` for README file enumeration
- **Code Search**: Excludes README files with `--exclude "**/readme.nix" --exclude "**/README.md"`

### Search Implementation

**Stage1 (README Filtering)**:
- Finds all `readme.nix` files in the project tree
- Uses ck to search README content for query matches
- Extracts parent directories as candidates for Stage2

**Stage2 (Code Search)**:
- Searches code files only within Stage1 candidate directories
- Uses ck with semantic search (`--sem`) and exclusions for README files
- Aggregates results across all candidate directories

## Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
nix run .#test

# Test output formats only
nix run .#test-formats

# Test exit codes only  
nix run .#test-exit-codes
```

### Test Coverage

1. **Format Tests**: Validates JSON/text output structure and content
2. **Exit Code Tests**: Verifies all exit codes behave as documented
3. **Integration Tests**: End-to-end pipeline mode validation
4. **Error Handling**: Tests error conditions and message formatting

## Development

### Development Environment

```bash
# Enter development shell
nix develop

# Build packages
nix build

# Validate flake structure
nix flake check
```

### Project Structure

```
search-readme/
├── flake.nix              # Main flake with minimal-ck-wrapper implementation
├── README.md              # This documentation
├── test-readmes/          # Test data for development
│   ├── project-a/readme.nix
│   ├── project-b/readme.nix
│   ├── data-processing/readme.nix
│   └── tools/cli-util/readme.nix
└── .ck/                   # ck search tool configuration
```

## Integration

### CI/CD Integration

The strict exit code policy makes this tool ideal for automation:

```bash
# Pipeline script example
if search-readme -m pipeline -f json "authentication" > results.json; then
  echo "Found authentication-related code in $(jq '.pipeline.stage2.count' results.json) locations"
else
  case $? in
    80) echo "No README files describe authentication responsibilities" ;;
    81) echo "No code found in authentication-responsible directories" ;;
    *) echo "Search error occurred" ;;
  esac
fi
```

### Monorepo Workflow

1. Document project responsibilities in `readme.nix` files
2. Use pipeline mode to find code within responsible projects
3. Leverage exit codes for conditional workflow execution
4. Parse JSON output for detailed result processing

## Future Development

This implementation serves as an MVP for README-filtered code search. Planned enhancements include:
- Advanced semantic search integration
- Performance optimization for large monorepos
- Enhanced README responsibility syntax
- Integration with additional search backends

## Contributing

1. Ensure all checks pass: `nix flake check`
2. Run the test suite: `nix run .#test`
3. Verify exit code behavior for new features
4. Update documentation for any interface changes

## License

This project follows the license terms of its dependencies.