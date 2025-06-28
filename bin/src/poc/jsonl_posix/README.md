# POSIX Safe File Appending Mechanism

A POSIX-compliant locking mechanism for safe concurrent file appending using atomic directory creation.

## Overview

- Uses `mkdir` atomic operation for process-safe locking
- Language and format agnostic - works with any file type
- No data format enforcement - handles raw file appending only
- All processes must use the same locking mechanism for safety

## Usage

### Basic Usage

```bash
#!/bin/bash
source ./lib/posix_lock.sh

# Append a single line
safe_append "This is a line of text" "myfile.txt"

# Use default file (set via APPEND_FILE environment variable)
export APPEND_FILE="default.log"
safe_append "Another line"

# Append from stdin
echo "Content from pipe" | safe_append_stdin "output.txt"
```

### Concurrent Usage

Multiple processes can safely append to the same file:

```bash
# Process 1
safe_append "Process 1 data" "shared.txt"

# Process 2 (running simultaneously)
safe_append "Process 2 data" "shared.txt"
```

## How It Works

1. Uses `mkdir` command's atomic property for exclusive locking
2. Only the process that successfully creates the lock directory gains write access
3. After appending, the lock directory is removed to release the lock
4. Includes timeout mechanism to prevent deadlocks

## Implementation Details

The locking mechanism relies on POSIX-compliant shell features:
- `mkdir` for atomic lock creation
- `/tmp` for lock directory location
- Simple sleep-based retry with timeout

## Important Notes

- All processes must use this locking mechanism when accessing the same file
- Direct file writes bypass the lock and may cause data corruption
- Lock files are created in `/tmp` with the pattern: `<filename>.lock`
- Default timeout is 5 seconds (configurable in the script)