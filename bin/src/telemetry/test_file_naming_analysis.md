# テストファイル名の分析と改善計画

## 現状

### Python (log_py)
- `test_behavior.py`: 振る舞いテスト（統合テスト）
- `test_variables.py`: 環境変数関連のユニットテスト

### TypeScript (log_ts)
- **テストファイルが存在しない**

## 問題点

1. TypeScriptにテストが未実装
2. Python/TypeScript間でテストカバレッジの差異

## 改善計画

### 1. TypeScriptテストの追加

必要なテストファイル:
- `test_behavior.ts`: Pythonの`test_behavior.py`に相当
- `test_variables.ts`: 環境変数関連のテスト
- `test_domain.ts`: ドメインロジックのユニットテスト
- `test_application.ts`: アプリケーション層のテスト

### 2. テストファイル命名規則

現在の命名規則は適切:
- `test_` プレフィックス: テストファイルであることを明示
- 機能別の命名: `behavior`, `variables` など
- 言語固有の拡張子: `.py`, `.ts`

### 3. 統一すべき点

- テストの構造と内容を両言語で一致させる
- 同じテストケースを両言語で実装
- テスト実行コマンドの統一（`nix run .#test`）

## 優先度

1. **高**: TypeScriptの基本的なテスト追加
2. **中**: 振る舞いテストの統一
3. **低**: 詳細なユニットテストの追加

## 次のアクション

1. TypeScriptに`test_behavior.ts`を追加
2. Denoのテストランナー設定
3. flake.nixのテストコマンド実装