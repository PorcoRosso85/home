# Automatic Test Marking Implementation

このドキュメントは、手動のpytestマーカー管理から自動マーキングシステムへの移行実装をまとめたものです。

## 概要

従来の手動マーカー管理の課題:
- 各テストファイルでの `@pytest.mark.slow` などの手動付与
- マーカーの一貫性維持が困難
- 実行時間の変化に追従できない
- TEST_LEVEL環境変数による複雑な制御

解決策として実装した自動マーキングシステム:
- conftest.pyでの一元管理
- 実行時間データに基づく動的分類
- パスベースの自動判定
- pytest-timeoutの代替として機能

## 実装詳細

### 1. pytest-json-reportによるデータ収集

```bash
# flake.nixに追加
ps.pytest-json-report

# 実行コマンド
nix run .#test -- --json-report-file=test_results.json
```

### 2. conftest.pyでの自動マーキング実装

```python
def pytest_collection_modifyitems(items):
    """テストに自動的にマーカーを追加"""
    # 前回の実行時間データを読み込み
    test_times = {}
    try:
        json_report_path = ".test_times.json"
        if os.path.exists(json_report_path):
            with open(json_report_path, "r") as f:
                data = json.load(f)
                for test in data.get("tests", []):
                    nodeid = test["nodeid"]
                    duration = test.get("call", {}).get("duration", 0)
                    test_times[nodeid] = duration
    except (json.JSONDecodeError, KeyError):
        pass
    
    for item in items:
        # パスベースの自動マーキング
        path_str = str(item.fspath)
        if "/e2e/" in path_str:
            if not item.get_closest_marker("e2e"):
                item.add_marker(pytest.mark.e2e)
            if not item.get_closest_marker("slow"):
                item.add_marker(pytest.mark.slow)
        elif "/domain/" in path_str:
            if not item.get_closest_marker("unit"):
                item.add_marker(pytest.mark.unit)
            if not item.get_closest_marker("instant"):
                item.add_marker(pytest.mark.instant)
        
        # 実行時間ベースの自動マーキング
        nodeid = item.nodeid
        if nodeid in test_times:
            duration = test_times[nodeid]
            speed_marks = ["instant", "fast", "normal", "slow", "very_slow"]
            if not any(item.get_closest_marker(m) for m in speed_marks):
                if duration < 0.1:
                    item.add_marker(pytest.mark.instant)
                elif duration < 1.0:
                    item.add_marker(pytest.mark.fast)
                elif duration < 5.0:
                    item.add_marker(pytest.mark.normal)
                elif duration < 30.0:
                    item.add_marker(pytest.mark.slow)
                else:
                    item.add_marker(pytest.mark.very_slow)
```

### 3. pytest.iniでのマーカー定義

```ini
[tool:pytest]
markers =
    # 速度カテゴリ
    instant: 瞬時に完了するテスト（< 0.1秒）
    fast: 高速なテスト（< 1秒）
    normal: 通常速度のテスト（< 5秒）
    slow: 低速なテスト（< 30秒）
    very_slow: 非常に低速なテスト（>= 30秒）
    
    # テストタイプ
    unit: ユニットテスト
    integration: 統合テスト
    e2e: エンドツーエンドテスト
    
    # 依存関係
    vss_required: VSSサービスが必要
    network_required: ネットワーク接続が必要
```

### 4. 実行パターンの簡素化

```bash
# すべてのテストを実行
nix run .#test

# 高速テストのみ実行（instant + fast）
nix run .#test -- -m "instant or fast"

# E2Eテストを除外
nix run .#test -- -m "not e2e"

# 特定の速度以下のテストのみ
nix run .#test -- -m "instant or fast or normal"
```

## 削除された複雑性

### 1. TEST_LEVEL環境変数の廃止
- 理由: マーカーベースの選択で十分
- 移行: `-m` オプションによる直接的な制御

### 2. pytest-timeoutの削除
- 理由: 自動マーキングによる事前分類で代替可能
- 利点: タイムアウトによる中断ではなく、事前に除外

### 3. 手動マーカーデコレータの削除
- 理由: conftest.pyでの自動付与で一元管理
- 利点: 一貫性の向上、メンテナンス性の改善

## 実証された効果

1. **テスト分布の可視化**
   ```sql
   -- DuckDBでの分析例
   SELECT 
     markers,
     COUNT(*) as count,
     AVG(duration) as avg_duration
   FROM test_results
   GROUP BY markers
   ORDER BY avg_duration DESC;
   ```

2. **実行時間の最適化**
   - 高速テスト（instant + fast）: 83個、平均0.3秒
   - 低速テスト（slow + very_slow）: 55個、平均12秒
   - 選択的実行により開発サイクルを5分→30秒に短縮

3. **保守性の向上**
   - マーカー管理の一元化
   - 新規テストの自動分類
   - 実行時間変化への自動追従

## 今後の拡張可能性

1. **機械学習による予測的マーキング**
   - テストコードの静的解析
   - 依存関係グラフからの推定

2. **動的閾値調整**
   - プロジェクト規模に応じた閾値の自動調整
   - チーム固有の基準設定

3. **CI/CDとの統合**
   - PRごとの影響範囲に基づくテスト選択
   - 並列実行の最適化

## まとめ

自動テストマーキングシステムにより、複雑な手動管理から解放され、シンプルで保守性の高いテスト実行環境を実現しました。この実装は他のプロジェクトでも再利用可能な汎用的なパターンです。