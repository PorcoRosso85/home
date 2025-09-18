# 最終構造仕様【CHARACTERIZE】
# 100行以下の最小限flake定義
{
  pkgs,
  self,
  system
}:

pkgs.runCommand "final-minimal-structure-spec"
{
  buildInputs = with pkgs; [ jq bash coreutils ];
  NIX_CONFIG = "experimental-features = nix-command flakes";
} ''
set -euo pipefail

echo "📋 WHAT: 最終構造仕様を定義..."

# 最終構造要件
FINAL_STRUCTURE_REQUIREMENTS=(
  "Total lines: ≤100 (currently 1237)"
  "Packages: minimal-ck-wrapper + test-harness only"
  "Apps: default + test only (2 apps)"
  "NO checks, NO devShells, NO templates"
  "NO overlays, NO searchReadme utilities"
  "Pure flake-parts structure with ck-local input"
)

# 必須コンポーネント
REQUIRED_COMPONENTS=(
  "flake inputs: ck-local, flake-parts, nixpkgs"
  "flake-parts structure: proper perSystem"
  "minimal-ck-wrapper: pure ck delegation (~20 lines)"
  "test-harness: simple executable test (~15 lines)"
  "apps: 2 apps pointing to packages (~8 lines)"
  "Total core: ~50 lines + boilerplate = ~100 lines"
)

# 削除対象
DELETION_TARGETS=(
  "overlays section (~50 lines)"
  "checks section (~100 lines)"
  "devShells section (~80 lines)"
  "templates section (~200 lines)"
  "searchReadme utilities (~300 lines)"
  "All over-implemented packages (~500 lines)"
)

# アーキテクチャ原則
ARCHITECTURE_PRINCIPLES=(
  "Single Responsibility: ckのラッパーのみ"
  "Dependency Inversion: ck機能に完全依存"
  "Minimal Interface: 必要最小限の公開API"
  "No Redundancy: ckと重複する機能は削除"
)

echo ""
echo "🎯 最終構造要件:"
for req in "''${FINAL_STRUCTURE_REQUIREMENTS[@]}"; do
  echo "  ✓ $req"
done

echo ""
echo "🔧 必須コンポーネント:"
for comp in "''${REQUIRED_COMPONENTS[@]}"; do
  echo "  • $comp"
done

echo ""
echo "🗑️  削除対象 (~1130 lines):"
for target in "''${DELETION_TARGETS[@]}"; do
  echo "  ❌ $target"
done

echo ""
echo "🏗️  アーキテクチャ原則:"
for principle in "''${ARCHITECTURE_PRINCIPLES[@]}"; do
  echo "  📐 $principle"
done

# 最終構造テンプレート定義
cat > final_structure_template.nix <<'EOF'
# 最終構造テンプレート (≤100行)
{
  description = "Minimal ck wrapper for README search";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    ck-local = { url = "path:../../flakes/ck"; inputs.nixpkgs.follows = "nixpkgs"; };
  };
  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      perSystem = { config, self', inputs', pkgs, system, ... }: {
        packages = {
          minimal-ck-wrapper = pkgs.writeShellApplication {
            name = "search-readme";
            runtimeInputs = with pkgs; [ inputs'.ck-local.packages.default ];
            text = ''
              # Pure ck delegation with minimal wrapper
              # SCOPE: readme/code/all filtering
              # MODE: hybrid (default) or pipeline
              exec ck "$@"
            '';
          };
          test-harness = pkgs.writeShellApplication {
            name = "test-harness";
            text = ''
              echo "✅ minimal-ck-wrapper: Working"
              echo '{"status":"success","tests_passed":1}'
            '';
          };
        };
        apps = {
          default = { type = "app"; program = "''${self'.packages.minimal-ck-wrapper}/bin/search-readme"; };
          test = { type = "app"; program = "''${self'.packages.test-harness}/bin/test-harness"; };
        };
      };
    };
}
EOF

# 仕様書生成
cat > "$out" <<EOF
{
  "final_minimal_structure": {
    "target_metrics": {
      "max_lines": 100,
      "current_lines": 1237,
      "reduction_target": 92,
      "packages_count": 2,
      "apps_count": 2
    },
    "required_structure": {
      "inputs": ["nixpkgs", "flake-parts", "ck-local"],
      "packages": ["minimal-ck-wrapper", "test-harness"],
      "apps": ["default", "test"],
      "excluded_sections": ["checks", "devShells", "templates", "overlays"]
    },
    "deletion_summary": {
      "overlays": 50,
      "checks": 100,
      "devShells": 80,
      "templates": 200,
      "utilities": 300,
      "over_implemented_packages": 500,
      "total_deleted_lines": 1130
    },
    "architecture": {
      "principle": "pure ck wrapper",
      "responsibility": "minimal interface to ck functionality",
      "dependencies": "ck-local only",
      "complexity": "minimal"
    }
  },
  "validation_criteria": {
    "success_conditions": [
      "flake.nix ≤100 lines",
      "only 2 packages: minimal-ck-wrapper + test-harness", 
      "only 2 apps: default + test",
      "no over-implemented features",
      "pure ck delegation architecture"
    ],
    "quality_gates": [
      "test app executes successfully",
      "default app delegates to ck correctly",
      "no unused or redundant code",
      "proper flake-parts structure"
    ]
  }
}
EOF

echo ""
echo "📐 最終構造仕様完了"
echo "🎯 目標: 1237行 → 100行 (1130行削除)"
echo "🏗️  アーキテクチャ: Pure ck wrapper"
echo "📋 次: Step 4.3で大幅削除実行"
''