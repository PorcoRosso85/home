# 簡素appsの仕様【CHARACTERIZE】
# 最小限ckラッパー用の2個アプリ仕様
{
  pkgs,
  self,
  system
}:

pkgs.runCommand "simple-apps-specification"
{
  buildInputs = with pkgs; [ jq bash coreutils ];
  NIX_CONFIG = "experimental-features = nix-command flakes";
} ''
set -euo pipefail

echo "🔧 Defining simple apps specification..."

# 仕様: 簡素apps構造の要件
SPEC_REQUIREMENTS=(
  "Only 2 apps: default + test"
  "default app points to minimal-ck-wrapper"
  "test app is simplified (no inline scripts)"
  "No optimized app (redundant with ck)"
  "No references to deleted packages (default, search-optimized)"
  "Total app definitions: ≤10 lines"
)

# 仕様: 簡素app構造
cat > simple_apps_structure.md << 'EOF'
# Simplified Apps Structure (≤10 lines)

## App 1: default (3 lines)
- Type: app
- Program: minimal-ck-wrapper/bin/search-readme

## App 2: test (4 lines)  
- Type: app
- Program: test-harness

## Removed Apps
- optimized (redundant with ck built-in optimization)
EOF

# 仕様: 削除するアプリ
REMOVAL_TARGETS=(
  "optimized app (points to search-optimized package)"
  "complex inline test script"
  "references to over-implemented packages"
)

echo ""
echo "📋 Simple apps specification:"
echo "Target: 2 apps, ≤10 lines total"
echo "Focus: minimal-ck-wrapper + simple test"

echo ""
echo "✅ Required app structure:"
for req in "''${SPEC_REQUIREMENTS[@]}"; do
  echo "  • $req"
done

echo ""
echo "🗑️  Removing excessive apps:"
for target in "''${REMOVAL_TARGETS[@]}"; do
  echo "  ❌ $target"
done

# 仕様書生成
cat > "$out" <<EOF
{
  "specification": {
    "name": "simple-apps",
    "max_lines": 10,
    "target_apps": ["default", "test"],
    "excluded_apps": ["optimized"],
    "required_structure": $(printf '%s\n' "''${SPEC_REQUIREMENTS[@]}" | jq -R . | jq -s .),
    "removed_features": $(printf '%s\n' "''${REMOVAL_TARGETS[@]}" | jq -R . | jq -s .),
    "app_definitions": {
      "default": {
        "type": "app", 
        "program": "minimal-ck-wrapper",
        "lines": 3
      },
      "test": {
        "type": "app",
        "program": "test-harness", 
        "lines": 4
      },
      "total_estimated_lines": 10
    }
  },
  "validation": {
    "passes_if": "apps ≤10 lines AND only default+test AND points to minimal-ck-wrapper",
    "fails_if": "includes optimized app OR >10 lines OR references deleted packages"
  }
}
EOF

echo "✨ Simple apps specification completed"
echo "📄 Specification saved to output"
''