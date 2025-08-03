# select-project Script

A standalone project selector script that uses `fzf` to select existing projects with `flake.nix` files or create new project directories.

## Features

- Interactive project selection using `fzf`
- Lists all `flake.nix` files recursively from a root directory
- Allows entering a custom path to create a new project
- Returns the selected/created project directory path
- Handles cancellation gracefully (exits with code 1)
- Debug mode for troubleshooting
- Works with or without `fzf` in PATH (falls back to `nix run`)

## Usage

```bash
./select-project [OPTIONS]
```

### Options

- `-h, --help`: Show help message
- `-d, --debug`: Enable debug logging
- `-r, --root DIR`: Start search from DIR (default: current directory)

### Exit Codes

- `0`: Success - project directory selected/created
- `1`: Cancelled or error occurred

## Examples

### Basic Usage

```bash
# Select a project
if project_dir=$(./select-project); then
  echo "Selected: $project_dir"
  cd "$project_dir"
else
  echo "No selection made"
fi
```

### With Custom Root Directory

```bash
# Search for projects under /home/nixos/bin
project_dir=$(./select-project --root /home/nixos/bin)
```

### With Debug Mode

```bash
# Enable debug output
DEBUG=1 ./select-project
# or
./select-project --debug
```

## Integration Example

See `example-launcher-integration.sh` for a complete example of how to integrate this script into a Claude launcher.

## fzf Interface

When running the script:
- **Enter**: Confirm selection
- **Tab**: Edit the current selection
- **Type a path**: Create a new project at that location
- **ESC**: Cancel selection

The preview window shows the first 20 lines of the selected `flake.nix` file.

## Testing

Run `./test-select-project.sh` to execute basic tests of the script functionality.