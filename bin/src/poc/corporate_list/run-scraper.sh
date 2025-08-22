#!/usr/bin/env bash
set -e

# Corporate List Scraper with Switchover Support
# 
# Usage:
#   ./run-scraper.sh                 # Uses TypeScript implementation (default)
#   USE_LEGACY=true ./run-scraper.sh # Uses legacy implementation
#

# Set up environment for Playwright
export PLAYWRIGHT_BROWSERS_PATH=$(nix-build --no-out-link '<nixpkgs>' -A chromium)
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Check if we're in a nix shell or need to enter one
if command -v node >/dev/null 2>&1; then
    # We're in a development shell, use npm script directly
    echo "🚀 Running from development environment"
    exec npm run scrape "$@"
else
    # Enter nix shell first
    echo "🔧 Entering nix development shell..."
    exec nix develop --command npm run scrape "$@"
fi