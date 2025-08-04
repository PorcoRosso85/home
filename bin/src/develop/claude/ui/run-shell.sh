#!/usr/bin/env bash
# run-shell.sh - Fast launcher using nix shell
# Performance: ~0.1s (3x faster than nix run)
# File access: ~50 files (vs 1000+ with nix run)

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a temporary launcher script that will be executed in the nix shell
launcher_script=$(cat << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# The scripts directory is passed as the first argument
SCRIPTS_DIR="$1"

# Run the project selector
project_dir=$("$SCRIPTS_DIR/select-project") || exit 1

# Check if this is an existing project
if [[ -f "$project_dir/flake.nix" ]]; then
  # Existing project - try to continue conversation
  exec "$SCRIPTS_DIR/launch-claude" "$project_dir" --continue
else
  # New project - start fresh
  exec "$SCRIPTS_DIR/launch-claude" "$project_dir"
fi
EOF
)

# Run with nix shell for optimal performance
exec nix shell \
  nixpkgs#fzf \
  nixpkgs#findutils \
  nixpkgs#coreutils \
  nixpkgs#gnugrep \
  nixpkgs#bash \
  --command bash -c "$launcher_script" -- "$SCRIPT_DIR/scripts"