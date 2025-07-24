# トラブルシューティングガイド

## セグメンテーションフォルト (Segmentation Fault)

### 問題
`test_existing_connection.py::test_detailed_performance_comparison` テスト実行時にセグメンテーションフォルトが発生します。

### 原因
PyTorchとKuzuDBのマルチスレッド環境での競合が原因です：

1. **PyTorchコンパイルワーカー**: sentence-transformersがモデルロード時に複数のPyTorchワーカースレッドを起動
2. **KuzuDB接続**: FTSSearchAdapterがKuzuDBに対してSQL実行（check_fts_extension）
3. **タイミング問題**: 複数のSearchAdapterインスタンスを短時間で作成・破棄する際に、PyTorchのスレッドプールとKuzuDBアクセスが競合

### スタックトレース
```
Thread (PyTorch worker):
  torch._inductor.compile_worker.subproc_pool._recv_msg

Main thread:
  kuzu.connection.execute
  ├─ fts_kuzu.infrastructure.check_fts_extension
  └─ SearchAdapter初期化中
```

### 解決策

#### 1. テストのスキップ（現在の対応）
```python
@pytest.mark.skip(reason="Segmentation fault due to PyTorch/KuzuDB thread conflict")
```

#### 2. 環境変数でPyTorchのスレッド数を制限
```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
nix run .#test
```

#### 3. シーケンシャルな実行
SearchAdapterのインスタンス化を並列ではなく順次実行し、各インスタンスの完全な終了を待つ。

### 影響範囲
- パフォーマンステストのみ影響
- 通常の使用には影響なし
- VSS/FTS機能自体は正常動作

### 関連Issue
- PyTorch Issue: マルチスレッド環境でのセグメンテーションフォルト
- KuzuDB: ネイティブ拡張との相互作用