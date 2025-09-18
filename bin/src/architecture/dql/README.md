# DQL (Data Query Language) ディレクトリ

アーキテクチャ分析のためのクエリ集を管理します。

## ディレクトリ構成

- **analysis/** - アーキテクチャ分析クエリ
  - 依存関係分析
  - 影響範囲分析
  - 複雑度分析
  
- **validation/** - 検証クエリ
  - 整合性チェック
  - 循環参照検出
  - 孤立ノード検出
  
- **reporting/** - レポート生成クエリ
  - 要件一覧レポート
  - 変更履歴レポート
  - 依存関係マトリクス

## クエリ命名規則

```
<目的>_<対象>_<アクション>.cypher
```

例:
- `analyze_dependencies_depth.cypher` - 依存関係の深さを分析
- `validate_circular_references.cypher` - 循環参照を検証
- `report_requirements_summary.cypher` - 要件サマリーをレポート

## 使用方法

```bash
# クエリ実行
python ../infrastructure/query_runner.py execute analysis/analyze_dependencies_depth.cypher

# パラメータ付き実行
python ../infrastructure/query_runner.py execute validation/validate_requirement.cypher --id "req_001"
```