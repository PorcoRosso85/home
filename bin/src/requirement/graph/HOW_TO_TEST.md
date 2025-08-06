# テスト実行ガイド

## 概要
requirement/graphのテストスイートは126個のテストを含み、完全実行には約20分かかります。
開発効率を向上させるため、状況に応じた適切なテストコマンドを使い分けてください。

## テストコマンド一覧

### 開発時（高速実行）
```bash
# 高速テストのみ実行（〜1分）
nix shell .# -c 'pytest -m "not slow and not very_slow"'

# 単体テストのみ（〜30秒）
nix shell .# -c 'pytest -m "unit"'

# ドメインロジックのみ（〜10秒）
nix shell .# -c 'pytest domain/'
```

### 機能別テスト
```bash
# 重複検出機能のテスト
nix shell .# -c 'pytest -k "duplicate_detection"'

# 検索機能のテスト
nix shell .# -c 'pytest -k "search"'

# 循環依存検出のテスト
nix shell .# -c 'pytest -k "circular"'
```

### 統合テスト
```bash
# E2Eテストを除外（〜5分）
nix shell .# -c 'pytest -m "not e2e"'

# 統合テストのみ
nix shell .# -c 'pytest -m "integration"'
```

### CI/完全実行
```bash
# すべてのテスト（〜20分）
nix shell .# -c 'pytest'

# 並列実行で高速化
nix shell .# -c 'pytest -n auto'

# 最も遅い10個のテストを表示
nix shell .# -c 'pytest --durations=10'
```

### デバッグ用
```bash
# 詳細な出力
nix shell .# -c 'pytest -vv'

# 最初のエラーで停止
nix shell .# -c 'pytest -x'

# 特定のテストのみ
nix shell .# -c 'pytest path/to/test_file.py::TestClass::test_method'
```

## テストマーカー

### 速度階層
- `instant`: < 0.1秒（純粋関数、単体テスト）
- `fast`: < 1秒（軽量統合テスト）
- `normal`: < 5秒（標準統合テスト）
- `slow`: < 30秒（重い統合テスト、E2E）
- `very_slow`: >= 30秒（非常に重いE2Eテスト）

### テストタイプ
- `unit`: 単体テスト（高速、独立）
- `integration`: データベースが必要な統合テスト
- `e2e`: サブプロセスを使用するエンドツーエンドテスト

### 依存関係
- `vss_required`: VSSサービス初期化が必要
- `db_required`: データベースアクセスが必要

## 推奨ワークフロー

1. **開発中**: `nix shell .# -c 'pytest -m "not slow and not very_slow"'`
2. **コミット前**: `nix shell .# -c 'pytest -m "not e2e"'`
3. **プルリクエスト**: `nix shell .# -c 'pytest'`（完全実行）

## パフォーマンスのヒント

- VSS/FTS初期化は時間がかかるため、関連テストは最小限に
- E2Eテストはサブプロセス起動のオーバーヘッドがある
- `--durations`オプションで遅いテストを特定可能

## トラブルシューティング

### テストが遅い場合
```bash
# 最も遅い20個のテストを確認
nix shell .# -c 'pytest --durations=20'

# プロファイリング付き実行
nix shell .# -c 'python -m cProfile -o profile.stats -m pytest'
```

### 特定のテストをスキップ
```bash
# VSSが必要なテストをスキップ
nix shell .# -c 'pytest -m "not vss_required"'
```