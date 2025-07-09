# POC Search - KuzuDB VSS/FTS/Hybrid Search

## テスト実行

```bash
cd /home/nixos/bin/src/poc/search
nix run .#test
```

## テストファイル

- `test_hybrid_complete.py` - 6つの実用シナリオのテスト
- `test_kuzu_native_features.py` - KuzuDBネイティブ機能の動作確認
- `test_kuzu_native_complete.py` - ネイティブ機能での完全実装

## 注意事項

- requirement/graph環境のPythonを使用
- KuzuDB v0.10.1のVECTOR/FTS拡張機能を使用
- インメモリDBで全テストを実行