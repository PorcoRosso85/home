# ブラックボックステスト仕様書

## 価値（WHY）

### 内部ロジックに依存しない契約検証
- アルゴリズムの実装方法に関係なく、契約準拠のみを検証
- コード変更時も契約さえ守れば他言語実装への影響なし
- 言語・フレームワーク・ライブラリに依存しない普遍的検証

### 言語非依存の契約検証システム
- Python/Rust/Go/Shell等、任意の言語で同じ契約を検証可能
- 出力されるJSON形式のみが検証対象
- 実装言語の制約を受けない柔軟な開発環境

## 仕様（WHAT）

### Producer/Consumerの出力契約準拠のみ検証
- JSONスキーマとして定義された契約への準拠性
- フィールドの型、必須項目、値の範囲制約
- ネストした構造やリスト項目の制約

### 内部実装は対象外
- `3+2=5`の計算ロジックの正しさは検証しない
- アルゴリズムの効率性や実装方法は評価対象外
- ビジネスロジックの妥当性は別途テストで担保

## 方法（HOW）

### 基本的な契約検証

任意の言語実装→JSON出力→Nickel契約検証

```bash
# Shell実装
./producer.sh | nickel eval "data & contracts.ProducerContract"

# Python実装  
python producer.py | nickel eval "data & contracts.ProducerContract"

# Rust実装
cargo run --bin producer | nickel eval "data & contracts.ProducerContract"

# Go実装
go run producer.go | nickel eval "data & contracts.ProducerContract"
```

### verify_any_implementation関数

```bash
verify_any_implementation() {
    local binary="$1"
    local contract="$2"
    $binary | nickel eval "let c = import 'contracts.ncl' in data & c.$contract"
}

# 使用例
verify_any_implementation "./producer.sh" "ProducerContract"
verify_any_implementation "python producer.py" "ConsumerContract"
verify_any_implementation "cargo run --bin producer" "DataContract"
```

### パイプラインでの検証

```bash
# 複数実装の一括検証
for impl in "./producer.sh" "python producer.py" "cargo run --bin producer"; do
    echo "Testing: $impl"
    verify_any_implementation "$impl" "ProducerContract"
done
```

## 使い方（CHECK）

### 実行環境前提

このブラックボックステストシステムは以下の環境を前提としています：

- **基本実行**: `nix flake check` - CI/CDや自動検証に推奨
- **手動実行**: `nix develop` 環境内 - 開発時のデバッグや単体実行時
- **テストスクリプト**: `nix develop -c nickel` でNickel契約検証を実行

混在する実行方法は、異なる用途（自動化 vs 手動）に対応した設計です。

### 自動実行
```bash
# Flakeベースの統合チェック
nix flake check

# 開発時の継続的検証
nix develop -c ./test/blackbox_test_suite.sh
```

### 手動実行
```bash
# ブラックボックステストスイート実行
./test/blackbox_test_suite.sh

# 特定の実装のみテスト
./test/test_producer_contract.sh

# 契約違反のデバッグモード
DEBUG=1 ./test/blackbox_test_suite.sh
```

### CI/CD統合
```bash
# GitHub Actions等での実行
nix flake check

# Docker環境での実行
docker run --rm -v $(pwd):/workspace nixos/nix nix flake check
```

## よくある落とし穴

### JSON→Nickelの埋め込み時のエスケープ問題
```bash
# ❌ 問題のあるパターン
echo '{"message": "Hello "world""}' | nickel eval "data & Contract"

# ✅ 正しいパターン  
echo '{"message": "Hello \"world\""}' | nickel eval "data & Contract"

# ✅ より安全な方法
jq -c . input.json | nickel eval "data & Contract"
```

### 標準入力/出力の扱い
```bash
# ❌ 出力が混在するケース
./producer.sh 2>&1 | nickel eval "data & Contract"  # エラー出力も含まれる

# ✅ 標準出力のみを契約検証
./producer.sh 2>/dev/null | nickel eval "data & Contract"

# ✅ エラー処理も含めた安全な検証
if output=$(./producer.sh 2>/dev/null); then
    echo "$output" | nickel eval "data & Contract"
else
    echo "Producer failed to generate output"
    exit 1
fi
```

### 非決定的出力への対応
```bash
# タイムスタンプなど変動する値がある場合
./producer.sh | jq 'del(.timestamp)' | nickel eval "data & Contract"

# UUIDなどのランダム値を正規化
./producer.sh | jq '.id = "normalized"' | nickel eval "data & Contract"
```

## デバッグとトラブルシューティング

### 契約違反の詳細確認
```bash
# 詳細なエラー情報付きで検証
./producer.sh | nickel eval --error-format=detailed "data & Contract"

# 段階的な検証（フィールド別）
./producer.sh | nickel eval "data.version & Number" # version フィールドのみ
./producer.sh | nickel eval "data.items & Array" # items フィールドのみ
```

### 出力形式の事前確認
```bash
# JSON形式の妥当性確認
./producer.sh | jq empty  # 正しいJSONかチェック

# スキーマの可読性確認
./producer.sh | jq . | head -20  # 出力内容の確認
```

## Strictモード拡張計画

### 現在の実装
- 無効なProducer入力の拒否検証
- 基本的な型制約チェック

### 将来の拡張予定
- **error_diagnostics.ncl統合**: 詳細制約検証
- **数値制約**: 非負値検証 (processed >= 0, failed >= 0)
- **配列制約**: 必要時の非空検証
- **構造化エラーレポート**: 契約違反の詳細診断

### 拡張方針
Strictモードでのみ有効にし、パフォーマンスと検証レベルのトレードオフを提供