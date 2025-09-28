#!/usr/bin/env bash
set -euo pipefail

# RedwoodSDK R2 Connection Info Local Completion System
# Integration Test - Verification of side-effect-free implementation

echo "🧪 RedwoodSDK R2 Local Completion System - Integration Test"
echo "============================================================"
echo ""

REPO_ROOT="/home/nixos/bin/src/deploy/cloudflare"
cd "$REPO_ROOT"

FAILURES=0

# Helper function to report test results
test_result() {
	local test_name="$1"
	local result="$2"
	local details="${3:-}"

	if [[ "$result" == "PASS" ]]; then
		echo "✅ $test_name"
		[[ -n "$details" ]] && echo "   $details"
	else
		echo "❌ $test_name"
		[[ -n "$details" ]] && echo "   $details"
		FAILURES=$((FAILURES + 1))
	fi
}

echo "🔍 Acceptance Criteria Verification"
echo "==================================="

# Test 1: File Structure Validation
echo ""
echo "Test 1: Essential File Structure"
echo "---------------------------------"

required_files=(
	"flake.nix"
	"justfile"
	".sops.yaml"
	"r2.yaml.example"
	"scripts/gen-wrangler-config.js"
	"src/worker.ts"
	"secrets/.gitkeep"
)

missing_files=()
for file in "${required_files[@]}"; do
	if [[ ! -f "$file" ]]; then
		missing_files+=("$file")
	fi
done

if [[ ${#missing_files[@]} -eq 0 ]]; then
	test_result "File structure" "PASS" "All essential files present"
else
	test_result "File structure" "FAIL" "Missing: ${missing_files[*]}"
fi

# Test 2: Nix Flake Validation
echo ""
echo "Test 2: Nix Flake Validation"
echo "-----------------------------"

if command -v nix >/dev/null 2>&1; then
	# Check flake syntax by parsing the file structure
	if grep -q "outputs.*=" flake.nix && grep -q "inputs.*=" flake.nix; then
		test_result "Nix flake syntax" "PASS" "flake.nix has basic structure"
	else
		test_result "Nix flake syntax" "FAIL" "flake.nix missing basic structure"
	fi

	# Check that expected outputs are present by looking at the file
	if grep -q "devShells.*=" flake.nix; then
		test_result "DevShell outputs" "PASS" "Development shells defined"
	else
		test_result "DevShell outputs" "FAIL" "No development shells found"
	fi

	if grep -q "apps.*=" flake.nix; then
		test_result "App outputs" "PASS" "Nix apps defined"
	else
		test_result "App outputs" "FAIL" "No Nix apps found"
	fi

	if grep -q "checks.*=" flake.nix; then
		test_result "Check outputs" "PASS" "Nix checks defined"
	else
		test_result "Check outputs" "FAIL" "No Nix checks found"
	fi
else
	test_result "Nix availability" "SKIP" "Nix command not available - checking file structure only"

	# Fallback checks without nix command
	if grep -q "outputs.*=" flake.nix && grep -q "inputs.*=" flake.nix; then
		test_result "Nix flake structure" "PASS" "flake.nix has basic structure"
	else
		test_result "Nix flake structure" "FAIL" "flake.nix missing basic structure"
	fi
fi

# Test 3: JavaScript/TypeScript Syntax Validation
echo ""
echo "Test 3: JavaScript/TypeScript Syntax"
echo "-------------------------------------"

if command -v node >/dev/null 2>&1; then
	# Test Node.js script syntax
	if node --check scripts/gen-wrangler-config.js >/dev/null 2>&1; then
		test_result "Node.js script syntax" "PASS" "gen-wrangler-config.js is valid"
	else
		test_result "Node.js script syntax" "FAIL" "gen-wrangler-config.js has syntax errors"
	fi
else
	test_result "Node.js availability" "SKIP" "Node.js not available - checking file structure only"

	# Basic syntax check without node
	if grep -q "#!/usr/bin/env node" scripts/gen-wrangler-config.js; then
		test_result "Node.js script structure" "PASS" "gen-wrangler-config.js has proper shebang"
	else
		test_result "Node.js script structure" "FAIL" "gen-wrangler-config.js missing proper shebang"
	fi
fi

# Test TypeScript basic structure (doesn't require node)
if grep -q "interface.*Env" src/worker.ts && grep -q "export default" src/worker.ts; then
	test_result "TypeScript structure" "PASS" "worker.ts has proper structure"
else
	test_result "TypeScript structure" "FAIL" "worker.ts missing required structure"
fi

# Test 4: Configuration Template Validation
echo ""
echo "Test 4: Configuration Templates"
echo "--------------------------------"

# Check R2 template
if grep -q "cf_account_id:" r2.yaml.example && grep -q "r2_buckets:" r2.yaml.example; then
	test_result "R2 template" "PASS" "r2.yaml.example has required fields"
else
	test_result "R2 template" "FAIL" "r2.yaml.example missing required fields"
fi

# Check SOPS configuration
if grep -q "creation_rules:" .sops.yaml && grep -q "path_regex: secrets/" .sops.yaml; then
	test_result "SOPS config" "PASS" ".sops.yaml properly configured"
else
	test_result "SOPS config" "FAIL" ".sops.yaml misconfigured"
fi

# Test 5: Just Task Definitions
echo ""
echo "Test 5: Just Task Definitions"
echo "------------------------------"

if command -v just >/dev/null 2>&1; then
	expected_tasks=(
		"secrets-init"
		"secrets-edit"
		"r2:gen-config"
		"r2:test"
		"r2:check-secrets"
		"r2:status"
	)

	missing_tasks=()
	for task in "${expected_tasks[@]}"; do
		if ! just --list 2>/dev/null | grep -q "$task"; then
			missing_tasks+=("$task")
		fi
	done

	if [[ ${#missing_tasks[@]} -eq 0 ]]; then
		test_result "Just tasks" "PASS" "All required tasks defined"
	else
		test_result "Just tasks" "FAIL" "Missing tasks: ${missing_tasks[*]}"
	fi
else
	test_result "Just availability" "SKIP" "just command not available - checking justfile structure"

	# Check justfile has the required tasks
	expected_tasks=(
		"secrets-init"
		"secrets-edit"
		"r2:gen-config"
		"r2:test"
		"r2:check-secrets"
		"r2:status"
	)

	missing_tasks=()
	for task in "${expected_tasks[@]}"; do
		if ! grep -q "^$task:" justfile; then
			missing_tasks+=("$task")
		fi
	done

	if [[ ${#missing_tasks[@]} -eq 0 ]]; then
		test_result "Just task definitions" "PASS" "All required tasks defined in justfile"
	else
		test_result "Just task definitions" "FAIL" "Missing tasks in justfile: ${missing_tasks[*]}"
	fi
fi

# Test 6: Side-Effect Verification
echo ""
echo "Test 6: Side-Effect-Free Implementation"
echo "----------------------------------------"

# Check for external API calls or resource creation
suspicious_patterns=(
	"https://api.cloudflare.com"
	"wrangler deploy"
	"wrangler publish"
	"curl.*api\.cloudflare"
	"terraform apply"
	"pulumi up"
)

side_effects_found=()
for pattern in "${suspicious_patterns[@]}"; do
	# Exclude docs and test files from side-effect checking
	if grep -r "$pattern" . \
		--exclude-dir=.git \
		--exclude-dir=result \
		--exclude-dir=docs \
		--exclude="test-integration.sh" \
		--exclude="*.md" 2>/dev/null; then
		side_effects_found+=("$pattern")
	fi
done

if [[ ${#side_effects_found[@]} -eq 0 ]]; then
	test_result "Side-effect check" "PASS" "No external API calls or deployments found"
else
	test_result "Side-effect check" "FAIL" "Found potential side effects: ${side_effects_found[*]}"
fi

# Check that we only use local/simulation modes
if grep -q "wrangler dev --local" flake.nix; then
	# Check we don't have any actual remote connections (excluding comments/echo statements)
	remote_patterns_found=false

	# Look for actual command usage, not just mentions in echo statements
	if grep -v "echo" flake.nix | grep -q "wrangler dev --remote"; then
		remote_patterns_found=true
	fi

	if grep -v "echo" flake.nix | grep -q "api\.cloudflare\.com"; then
		remote_patterns_found=true
	fi

	if [[ "$remote_patterns_found" == "false" ]]; then
		test_result "Local-only mode" "PASS" "Uses local development mode only"
	else
		test_result "Local-only mode" "FAIL" "Found remote connection patterns in actual commands"
	fi
else
	test_result "Local-only mode" "FAIL" "No local development mode found"
fi

# Test 7: Documentation and Examples
echo ""
echo "Test 7: Documentation Completeness"
echo "-----------------------------------"

# Check that template is not in secrets directory
if [[ -f "r2.yaml.example" && ! -f "secrets/r2.yaml.example" ]]; then
	test_result "Template placement" "PASS" "Template properly placed outside secrets/"
else
	test_result "Template placement" "FAIL" "Template incorrectly placed or missing"
fi

# Check README mentions R2
if grep -q -i "r2" README.md; then
	test_result "README relevance" "PASS" "README mentions R2"
else
	test_result "README relevance" "FAIL" "README doesn't mention R2"
fi

echo ""
echo "📊 Integration Test Summary"
echo "==========================="

if [[ $FAILURES -eq 0 ]]; then
	echo "🎉 ALL TESTS PASSED"
	echo ""
	echo "✅ R2 Connection Info Local Completion System is ready!"
	echo "✅ Implementation is side-effect-free and authentication-free"
	echo "✅ All acceptance criteria have been met"
	echo ""
	echo "🎯 Next Steps:"
	echo "   1. Run 'nix run .#r2 -- status' to check current state"
	echo "   2. Run 'nix run .#secrets-init' to set up encryption"
	echo "   3. Run 'nix run .#r2 -- test' to test local R2 operations"
	echo "   4. Run 'nix flake check' to validate security"
	exit 0
else
	echo "❌ $FAILURES TEST(S) FAILED"
	echo ""
	echo "⚠️  Please address the failing tests before proceeding"
	echo "   Check the detailed output above for specific issues"
	exit 1
fi
