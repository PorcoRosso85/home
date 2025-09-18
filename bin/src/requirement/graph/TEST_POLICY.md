# Test Policy

## 削除したファイル (2025-08-03)

以下のファイルを削除しました：
- `test_vss_fts_integration.py` - VSS/FTS統合テスト
- `test_vss_integration.py` - VSS単体の統合テスト
- `test_fts_integration.py` - FTS単体の統合テスト

## 責務分離の原則

### 各コンポーネントの責務
- **requirement/graph**: 要件グラフの管理とクエリ実行
- **search/vss**: ベクトル類似度検索の実装
- **search/fts**: 全文検索の実装

### テスト配置の原則
- 各コンポーネントは自身の責務に関するテストのみを持つ
- 他コンポーネントの機能に依存するテストは作成しない
- 統合テストは専用のディレクトリ（例：`poc/`）に配置

## 今後のテスト作成指針

### 許可されるテスト
1. **単体テスト**: コンポーネント内部のロジックテスト
2. **インターフェーステスト**: 公開APIの動作確認
3. **エラーハンドリングテスト**: 異常系の処理確認

### 禁止されるテスト
1. **他コンポーネント依存テスト**: VSS/FTSなど外部機能を使うテスト
2. **統合テスト**: 複数コンポーネントをまたぐテスト
3. **E2Eテスト**: システム全体の動作確認

## VSS/FTS統合テストの扱い方

### 配置場所
- `poc/`ディレクトリ内の専用プロジェクトとして作成
- 例：`poc/requirement_search_integration/`

### 実装方法
```python
# poc/requirement_search_integration/test_integration.py
# 各コンポーネントを明示的にインポート
from requirement.graph import RequirementGraph
from search.vss import VSSSearch
from search.fts import FTSSearch

# 統合テストの実装
```

### 管理方針
- 各コンポーネントのバージョンを明示的に管理
- 統合テストの失敗は各コンポーネントの問題として切り分け
- 定期的な実行とレポート生成

## まとめ

この方針により：
1. 各コンポーネントの責務が明確になる
2. テストの保守性が向上する
3. 依存関係が適切に管理される
4. 統合テストの目的と配置が明確になる