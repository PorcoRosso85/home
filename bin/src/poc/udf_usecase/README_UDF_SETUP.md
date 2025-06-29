# KuzuDB UDF 最小動作環境

## セットアップ完了内容

1. **ドキュメント保存**: `/home/nixos/bin/src/poc/2025-06-29_kuzu-python-udf.md`
2. **テスト環境**: `/home/nixos/bin/src/poc/kuzu_udf/`
3. **動作確認済みテスト**: `test_minimal_udf.py`

## 実行方法

```bash
cd /home/nixos/bin/src/poc/kuzu_udf
nix-shell --run "uv run python test_minimal_udf.py"
# または
nix-shell --run "uv run pytest test_minimal_udf.py -v"
```

## テスト内容

1. **Simple UDF** - 整数に10を加算するUDF
2. **String UDF** - 文字列を大文字に変換するUDF  
3. **Typed UDF** - 明示的な型指定での乗算UDF

## 重要な発見

- NixOS環境では`libstdc++.so.6`が必要
- `shell.nix`でLD_LIBRARY_PATHを設定することで解決
- QueryResultはiterableではないため、`has_next()`と`get_next()`を使用

## 次のステップ

これで`/tdd_red`コマンドを実行する準備が整いました。