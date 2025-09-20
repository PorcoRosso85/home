# Tier 0 Index Specification - Precise Implementation Guide

## Record Format Specification

### JSONL Record Schema (Required)

```json
{
  "dir": "/absolute/path/to/project",
  "dirHash": "sha256_prefix_16_chars",
  "hostPort": "host:port",
  "session": "ses_session_id_string",
  "created": "epoch_timestamp_string"
}
```

### Field Specifications

| Field | Type | Format | Constraint | Example |
|-------|------|--------|------------|---------|
| `dir` | string | absolute path | Must start with `/` | `"/home/user/project"` |
| `dirHash` | string | SHA256 prefix | 16 characters, hex | `"a1b2c3d4e5f6g7h8"` |
| `hostPort` | string | host:port | `^[^:]+:[0-9]+$` | `"127.0.0.1:4096"` |
| `session` | string | OpenCode SID | Must start with `ses_` | `"ses_abc123def456"` |
| `created` | string | Unix timestamp | Numeric string | `"1695123456"` |

### Field Generation Rules

#### `dir` Field
- **Source**: `realpath()` output of project directory
- **Normalization**: Remove trailing slash if present
- **Constraint**: Must be absolute path (starts with `/`)

#### `dirHash` Field
- **Generation**: `sha256(dir)` truncated to first 16 characters
- **Purpose**: Collision-resistant short identifier for path-based indexing
- **Format**: Lowercase hexadecimal

#### `hostPort` Field
- **Source**: Normalized from OPENCODE_URL
- **Processing**: Extract host:port from URL, remove protocol/path
- **Example**: `http://127.0.0.1:4096/api` → `"127.0.0.1:4096"`

#### `session` Field
- **Source**: OpenCode session ID from server response
- **Constraint**: Must match OpenCode session ID format (`ses_*`)
- **Validation**: Verified against server before recording

#### `created` Field
- **Source**: Unix timestamp at record creation time
- **Format**: String representation of epoch seconds
- **Purpose**: Audit trail and potential cleanup sorting

## Uniqueness Constraint Specification

### Primary Key Definition
**Uniqueness Key**: `(hostPort, dirHash, session)`

### Constraint Logic
```bash
uniqueness_key = hostPort + "|" + dirHash + "|" + session
```

### Duplicate Detection Rules
1. **Same Key = Duplicate**: Records with identical `(hostPort, dirHash, session)` are duplicates
2. **Different `dir`**: Not considered in uniqueness (allows path moves)
3. **Different `created`**: Not considered in uniqueness (allows timestamp updates)

### Constraint Scope (Tier 0)
- **Process-Scoped**: Uniqueness enforced within single process memory
- **Memory Set**: Use in-memory set to track seen uniqueness keys
- **Append Prevention**: Skip writing if uniqueness key already exists in memory set

### Multi-Process Considerations (Future Tiers)
- **Tier 1**: Light file locking for multi-process coordination
- **Tier 2**: Explicit locking with atomic read-check-write operations

## Corruption Handling Specification

### Broken Line Detection
- **Method**: Attempt JSON parsing on each line
- **Failure**: `jq .` or equivalent JSON parser returns non-zero exit code

### Recovery Strategy
```bash
# Pseudo-code for read_safe implementation
while read line; do
    if echo "$line" | jq . >/dev/null 2>&1; then
        process_valid_line "$line"
    else
        log_warning "Skipping broken line: $line"
        continue  # Skip broken line, continue processing
    fi
done
```

### Tail Parsing Optimization
- **Read Strategy**: Process from file end backwards when possible
- **Benefit**: Recent records first, early termination on sufficient data
- **Implementation**: Use `tail -n N` to limit parsing scope for large files

### Partial Recovery Guarantees
- **Minimum Viable**: System continues if ≥1 valid line exists
- **Degraded Mode**: Full functionality with reduced historical data
- **No Fatal Errors**: Broken lines never crash the system

## Path Normalization Specification

### Directory Path Processing
```bash
# Normalization pipeline
normalize_dir_path() {
    local input_path="$1"
    local normalized

    # Step 1: Resolve to absolute path
    normalized=$(cd "$input_path" && pwd 2>/dev/null)

    # Step 2: Remove trailing slash
    normalized="${normalized%/}"

    echo "$normalized"
}
```

### Host:Port Processing
```bash
# Host:port extraction from URL
normalize_host_port() {
    local url="$1"
    local host_port

    # Remove protocol
    host_port="${url#*://}"

    # Remove path
    host_port="${host_port%%/*}"

    echo "$host_port"
}
```

### Hash Generation
```bash
# Directory hash generation
generate_dir_hash() {
    local dir_path="$1"
    echo -n "$dir_path" | sha256sum | cut -c1-16
}
```

## File Operations Specification

### Append Operation (Tier 0)
```bash
# Simple append (no atomic guarantees in Tier 0)
echo "$json_record" >> "$index_file"
```

### Read Operation
```bash
# Line-by-line processing with error handling
while IFS= read -r line; do
    if [[ -n "$line" ]] && echo "$line" | jq . >/dev/null 2>&1; then
        # Process valid line
        process_index_record "$line"
    fi
done < "$index_file"
```

### Index File Location
- **Path**: `${session_base}/index.jsonl`
- **Where**: `session_base = ${XDG_STATE_HOME}/opencode/sessions`
- **Structure**: Single file for all host:port combinations in Tier 0

## API Function Specifications

### Core Functions (Required Implementation)

#### `oc_session_index_append()`
```bash
# Append new record with uniqueness check
oc_session_index_append() {
    local dir="$1"
    local hostPort="$2"
    local session="$3"

    # Normalize inputs
    # Generate record
    # Check uniqueness
    # Append to index
}
```

#### `oc_session_index_lookup_by_sid()`
```bash
# Find record by session ID
oc_session_index_lookup_by_sid() {
    local session="$1"

    # Search index for matching session
    # Return JSON record or empty
}
```

#### `oc_session_index_read_safe()`
```bash
# Read all valid records, skip broken lines
oc_session_index_read_safe() {
    # Process file line by line
    # Skip broken JSON lines
    # Output valid records only
}
```

### Utility Functions (Required Implementation)

#### `oc_session_index_normalize_dir()`
```bash
# Directory path normalization
oc_session_index_normalize_dir() {
    local input_path="$1"
    # Apply normalization rules
    # Return normalized absolute path
}
```

#### `oc_session_index_normalize_hostport()`
```bash
# Host:port normalization
oc_session_index_normalize_hostport() {
    local url="$1"
    # Extract and normalize host:port
    # Return normalized host:port
}
```

## Error Handling Contract

### Function Return Codes
- **0**: Success, operation completed
- **1**: Failure, operation could not complete
- **2**: Invalid input parameters

### Output Streams
- **stdout**: Data output only (JSON records, lookup results)
- **stderr**: Log messages, warnings, errors
- **Format**: `[function_name] level: message`

### Error Message Format
```bash
echo "[oc_session_index_append] error: duplicate record detected" >&2
echo "[oc_session_index_read_safe] warning: skipping broken line 42" >&2
```

## Performance Characteristics (Tier 0)

### Expected Scale
- **Sessions**: 1,000 - 10,000 records
- **File Size**: <1MB typical, <10MB maximum reasonable
- **Search Time**: O(n) linear search (acceptable for Tier 0 scale)

### Degradation Points
- **10,000+ records**: Consider Tier 1 (monthly rotation)
- **100,000+ records**: Consider Tier 3 (SQLite indexing)
- **Multiple processes**: Consider Tier 1 (file locking)

## Testing Requirements

### Unit Test Coverage
1. **Record Format**: All field types and constraints
2. **Uniqueness**: Duplicate detection and prevention
3. **Corruption**: Broken line handling and recovery
4. **Normalization**: Path and host:port processing

### Integration Test Coverage
1. **End-to-End**: Append → lookup → verify cycle
2. **Concurrency**: Single process multiple operations
3. **Recovery**: Index rebuild from session files

### Acceptance Criteria
- **All specification tests pass**: `test_tier0_index_spec.sh` GREEN
- **Real session integration**: Works with actual OpenCode sessions
- **Corruption resilience**: Handles various corruption scenarios
- **Performance baseline**: <100ms operations for typical scale

---

*Specification Version: 1.0*
*Implementation Target: Tier 0 (Minimal Viable Product)*
*Next Review: Upon Tier 1 requirements emergence*