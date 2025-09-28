#!/usr/bin/env bash
set -euo pipefail

# Comprehensive static check for "just" command usage
# Detects just command patterns while allowing legitimate references

echo "🔍 Scanning for 'just' command usage patterns..."

# Exit code tracking
violations=0

# Define patterns
JUST_COMMAND_PATTERN='just\s+[a-zA-Z0-9:_-]+'
ALLOW_PATTERNS="just \\(command runner\\)|just like|just because|just\\s*$|\"just\"|'just'|`just`"

# Define file scopes to check
SCOPES=(
	"README*"
	"docs/"
	"*.md"
	"test-*"
	"tests/"
	"*test*"
	"scripts/"
	"flake.nix"
)

# Function to check a single file
check_file() {
	local file="$1"

	# Skip binary files using file extension checks (since 'file' command may not be available)
	case "$file" in
	*.so | *.dylib | *.dll | *.exe | *.bin | *.o | *.a | *.tar | *.gz | *.zip | *.jpg | *.jpeg | *.png | *.gif | *.pdf)
		return 0
		;;
	esac

	# Skip .git and result directories
	if [[ "$file" == */.git/* ]] || [[ "$file" == */result/* ]]; then
		return 0
	fi

	# Find potential violations
	local matches
	matches=$(grep -n -E "$JUST_COMMAND_PATTERN" "$file" 2>/dev/null || true)

	if [[ -n "$matches" ]]; then
		# Check each match against allow patterns
		while IFS= read -r line; do
			local line_content
			line_content=$(echo "$line" | cut -d: -f2-)

			# Check if this line matches any allowed pattern
			if ! echo "$line_content" | grep -qE "$ALLOW_PATTERNS"; then
				echo "❌ VIOLATION in $file:"
				echo "   $line"
				violations=$((violations + 1))
			fi
		done <<<"$matches"
	fi
}

# Function to scan directory recursively
scan_directory() {
	local dir="$1"
	if [[ -d "$dir" ]]; then
		find "$dir" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.nix" -o -name "*.sh" -o -name "*.js" -o -name "*.ts" -o -name "README*" \) | while read -r file; do
			check_file "$file"
		done
	fi
}

# Main scanning logic
echo "Checking scopes: ${SCOPES[*]}"

for scope in "${SCOPES[@]}"; do
	if [[ "$scope" == *"/" ]]; then
		# Directory scope
		scan_directory "$scope"
	else
		# File pattern scope
		find . -maxdepth 3 -name "$scope" -type f 2>/dev/null | while read -r file; do
			check_file "$file"
		done
	fi
done

# Special case: Check shellHook in flake.nix
if [[ -f "flake.nix" ]]; then
	echo "Checking shellHook in flake.nix..."
	shellhook_content=$(sed -n '/shellHook\s*=/,/};/p' flake.nix 2>/dev/null || true)
	if echo "$shellhook_content" | grep -qE "$JUST_COMMAND_PATTERN"; then
		# Check against allow patterns
		shellhook_violations=$(echo "$shellhook_content" | grep -nE "$JUST_COMMAND_PATTERN" | grep -vE "$ALLOW_PATTERNS" || true)
		if [[ -n "$shellhook_violations" ]]; then
			echo "❌ VIOLATION in flake.nix shellHook:"
			echo "$shellhook_violations"
			violations=$((violations + 1))
		fi
	fi
fi

# Results
if [[ $violations -gt 0 ]]; then
	echo ""
	echo "❌ STATIC CHECK FAILED: Found $violations 'just' command usage(s)"
	echo ""
	echo "📋 Detected patterns that should be replaced:"
	echo "   • 'just command-name' → Use nix commands instead"
	echo "   • References to justfile → Update to nix-based approach"
	echo ""
	echo "✅ Allowed patterns (these are OK):"
	echo "   • 'just (command runner)' - tool references"
	echo "   • 'just like', 'just because' - natural language"
	echo "   • Quoted 'just' in documentation"
	echo ""
	echo "🔧 To fix violations:"
	echo "   1. Replace 'just command' with 'nix run .#command'"
	echo "   2. Update documentation to reference nix commands"
	echo "   3. Remove justfile references"
	exit 1
else
	echo "✅ No 'just' command violations detected"
	echo "🔐 Static check validation: PASSED"
fi
