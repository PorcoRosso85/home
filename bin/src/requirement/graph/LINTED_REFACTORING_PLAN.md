# Linter導入とリファクタリング計画

## 現状
- **総エラー数**: 3,584個
- **自動修正可能**: 2,953個（82.4%）
- **手動修正必要**: 631個（17.6%）

### 自動修正可能なエラー（[*]マーク付き）
| コード | 説明 | 件数 | 修正内容 |
|--------|------|------|----------|
| W292 | ファイル末尾の改行なし | 107 | 改行追加 |
| W291 | 行末の空白 | 82 | 空白削除 |
| F541 | f-stringにプレースホルダーなし | 20 | 通常の文字列に変換 |
| B905 | zip()でstrict指定なし | 3 | strict=False追加 |
| **合計** | | **212** | |

### 手動修正が必要な主要エラー
| コード | 説明 | 件数 | 対応方法 |
|--------|------|------|----------|
| W293 | 空白行に空白文字 | 2841 | エディタ設定で対応可能 |
| F401 | 未使用import | 172 | 削除が必要 |
| N802 | 関数名が規約違反 | 124 | snake_caseに変更 |
| E501 | 行が長すぎる（>120文字） | 52 | 改行で分割 |
| F841 | 未使用変数 | 41 | 削除または使用 |
| C901 | 複雑度が高い | 25 | リファクタリング必要 |

## 設定済み内容
```toml
# pyproject.toml
[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-nested-blocks = 4
```

## コマンド一覧
```bash
# 基本コマンド
nix run .#lint              # lint実行
nix run .#lint.stats        # エラー統計を表示

# 自動修正コマンド
nix run .#lint.preview      # 修正内容をプレビュー（変更なし）
nix run .#lint.fix          # 安全な自動修正を実行
nix run .#lint.fix-unsafe   # より多くの自動修正（要確認）

# その他
nix run .#format            # コードフォーマット
nix run .#lint -- --select C901  # 特定ルールのみチェック
```

## 自動修正可能なエラーの詳細

### 安全に自動修正可能（`lint.fix`で修正）
- **W291, W292, W293**: 空白関連（行末、ファイル末尾、空白行）
- **F541**: f-stringの不要な使用
- **B905**: zip()のstrict引数

### より積極的な自動修正（`lint.fix-unsafe`で修正）
- 一部のimport順序
- 型アノテーションの形式
- その他のコードスタイル

### 完全に手動修正が必要
- **F401**: 未使用import（削除判断が必要）
- **N802**: 関数名規約（APIの互換性考慮）
- **C901**: 複雑度（ロジックの再設計必要）
- **F841**: 未使用変数（削除or使用判断）

## リファクタリング実行順序

### Phase 1: 自動修正（即実行可能）
```bash
# 1. バックアップ作成
git add -A && git commit -m "feat: linter設定追加（リファクタリング前）"

# 2. 修正内容をプレビュー
nix run .#lint.preview | less

# 3. 安全な自動修正を実行
nix run .#lint.fix

# 4. 差分確認
git diff

# 5. テスト確認
nix run .#test

# 6. 問題なければコミット
git add -A && git commit -m "style: 安全な自動修正（空白、改行等）"

# 7. より積極的な修正が必要な場合
nix run .#lint.fix-unsafe
git diff  # 必ず差分を確認
nix run .#test
git add -A && git commit -m "style: 追加の自動修正（要レビュー）"
```

### Phase 2: import整理（低リスク）
```bash
# 未使用importを確認
nix run .#lint -- --select F401

# 手動で削除後、テスト実行
nix run .#test
```

### Phase 3: 複雑度の高い関数をリファクタリング（優先順位順）

#### 優先度1: 最も複雑な関数
| ファイル | 関数名 | 複雑度 | 対応方針 |
|---------|--------|--------|----------|
| application/autonomous_decomposer.py | create_autonomous_decomposer | 44 | 戦略パターンで分割 |
| application/scoring_service.py | create_scoring_service | 37 | ドメイン層に移動済みの部分を削除 |
| application/requirement_service.py | create_requirement_service | 30 | 各操作を個別関数に分割 |

#### 優先度2: 中程度の複雑度
| ファイル | 関数名 | 複雑度 | 対応方針 |
|---------|--------|--------|----------|
| application/scoring_service.py | calculate_friction_score | 19 | 摩擦タイプ別に関数分割 |
| domain/friction_calculator.py | calculate_friction_score | 16 | 既に分割候補あり |
| application/friction_detector.py | create_friction_detector | 13 | 検出ロジックを分離 |

### Phase 4: 命名規則修正（破壊的変更）
```bash
# 関数名の修正（N802）
nix run .#lint -- --select N802

# snake_caseに統一
# 影響範囲が大きいため、モジュール単位で実施
```

## 具体的なリファクタリング例

### autonomous_decomposer.py の分割案
```python
# Before: 複雑度44
def create_autonomous_decomposer(repository):
    def decompose_requirement(...):
        # 500行の巨大関数
        
# After: 各関数を複雑度10以下に
def create_autonomous_decomposer(repository):
    strategies = {
        "hierarchical": HierarchicalStrategy(repository),
        "functional": FunctionalStrategy(repository),
        "temporal": TemporalStrategy(repository),
    }
    
    def decompose_requirement(...):
        # 複雑度5程度のディスパッチャー
        strategy = strategies.get(decomposition_strategy)
        if not strategy:
            return error_response(...)
        return strategy.decompose(requirement)
```

## 進捗管理

### 完了基準
- [ ] Phase 1: 自動修正完了
- [ ] Phase 2: 未使用import 0個
- [ ] Phase 3: C901違反 0個
- [ ] Phase 4: N802違反 50%以下

### 次回再開時の確認コマンド
```bash
# 現在のエラー数を確認
nix run .#lint -- --statistics | tail -20

# 複雑度違反のみ確認
nix run .#lint -- --select C901 | grep "C901" | wc -l

# テストの実行
nix run .#test
```

## 自動修正と手動修正の判断基準

### Ruffで完全自動化可能（機械的な修正）
- **空白・改行系**: W291, W292, W293
- **フォーマット系**: 引用符、インデント
- **明らかなミス**: F541（空のf-string）

### 判断が必要で手動修正
- **未使用コード**: F401（import）、F841（変数）→ 本当に不要か確認
- **命名規則**: N802 → API互換性の考慮
- **複雑度**: C901 → アーキテクチャレベルの設計変更

## 注意事項
1. **各フェーズ後にテスト実行**を必須とする
2. **破壊的変更は小さく分割**してコミット
3. **既存の挙動を変えない**ようリファクタリング
4. 複雑度を下げる際は**ビジネスロジックの分離**を意識
5. **`lint.preview`で必ず確認**してから修正実行

## 未解決の課題
- scoring_service.pyとscoring_service_refactored.pyの重複
- domainとapplication層の責務が曖昧な部分
- テストコードのlintエラー（後回し推奨）