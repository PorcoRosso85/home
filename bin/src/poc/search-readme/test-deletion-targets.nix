# 削除対象パッケージの特性テスト【CHARACTERIZE】
# Feathers流: 現状を保護してから安全に削除
{
  pkgs,
  self,
  system
}:

pkgs.runCommand "deletion-targets-characterization-test"
{
  buildInputs = with pkgs; [ jq bash coreutils ];
  NIX_CONFIG = "experimental-features = nix-command flakes";
} ''
set -euo pipefail

echo "🔍 Characterizing packages for deletion..."

# 現在存在するパッケージを記録
echo "📦 Current packages:"
PACKAGES=$(nix eval ${self}#packages.${system} --apply 'pkgs: builtins.attrNames pkgs' --json)
echo "$PACKAGES" | jq -r '.[]' | sort

# 削除対象パッケージの定義
DELETION_TARGETS=(
  "search-report"     # ヘルスメトリクス - ckラッパーに不要
  "search-optimized"  # 最適化機能 - ckが提供
  "default"          # 過剰実装 - minimal-ck-wrapperに置換
  "test-harness"     # 過剰テスト - 簡素化必要
)

# 保持対象パッケージの定義  
PRESERVED_PACKAGES=(
  "minimal-ck-wrapper"         # 最小限ckラッパー（核心機能）
  "test-minimal-ck-wrapper"    # 最小限ラッパーテスト
  "flake-check"               # フレーク検証
)

echo ""
echo "🗑️  Deletion targets:"
for pkg in "''${DELETION_TARGETS[@]}"; do
  if echo "$PACKAGES" | jq -e --arg pkg "$pkg" 'any(. == $pkg)' >/dev/null; then
    echo "  ✓ $pkg (exists, will be deleted)"
  else
    echo "  ✗ $pkg (not found)"
  fi
done

echo ""
echo "💎 Preserved packages:"
for pkg in "''${PRESERVED_PACKAGES[@]}"; do
  if echo "$PACKAGES" | jq -e --arg pkg "$pkg" 'any(. == $pkg)' >/dev/null; then
    echo "  ✓ $pkg (exists, will be preserved)"
  else
    echo "  ✗ $pkg (missing - ERROR)"
    exit 1
  fi
done

# 削除前の機能確認（特性記録）
echo ""
echo "🧪 Pre-deletion functionality check:"

# minimal-ck-wrapper の動作確認（保持すべき機能）
echo "Testing minimal-ck-wrapper functionality..."
if nix build ${self}#packages.${system}.minimal-ck-wrapper -o test-wrapper 2>/dev/null; then
  if ./test-wrapper/bin/search-readme --scope all "test" . 2>/dev/null >/dev/null; then
    echo "  ✓ minimal-ck-wrapper: Basic functionality works"
  else
    echo "  ✗ minimal-ck-wrapper: Basic functionality failed"
    exit 1
  fi
else
  echo "  ✗ minimal-ck-wrapper: Build failed"
  exit 1
fi

# default パッケージの存在確認（削除対象）
echo "Checking deletion targets..."
for pkg in "''${DELETION_TARGETS[@]}"; do
  if nix build ${self}#packages.${system}.$pkg -o "test-$pkg" 2>/dev/null; then
    echo "  ✓ $pkg: Exists (ready for deletion)"
  else
    echo "  ? $pkg: Build failed (may already be deleted)"
  fi
done

# 特性レポート生成
cat > "$out" <<EOF
{
  "status": "characterized",
  "deletion_targets": $(printf '%s\n' "''${DELETION_TARGETS[@]}" | jq -R . | jq -s .),
  "preserved_packages": $(printf '%s\n' "''${PRESERVED_PACKAGES[@]}" | jq -R . | jq -s .),
  "pre_deletion_state": {
    "minimal_ck_wrapper_functional": true,
    "total_packages": $(echo "$PACKAGES" | jq 'length'),
    "packages_to_delete": ''${#DELETION_TARGETS[@]},
    "packages_to_preserve": ''${#PRESERVED_PACKAGES[@]}
  },
  "deletion_plan": {
    "step1": "Remove search-report (health metrics)",
    "step2": "Remove search-optimized (redundant with ck)",
    "step3": "Remove default (replace with minimal-ck-wrapper)",
    "step4": "Simplify test-harness"
  }
}
EOF

echo "✨ Characterization completed - ready for safe deletion"
''