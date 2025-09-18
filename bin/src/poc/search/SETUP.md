# Search PoC セットアップガイド

## クイックスタート

```bash
# 1. このディレクトリに移動
cd /home/nixos/bin/src/poc/search

# 2. 環境準備（初回のみ）
bash run_with_kuzu.sh echo "Environment setup complete"

# 3. データベース初期化（初回のみ）
cd /home/nixos/bin/src/data/kuzu && python setup.py
cd -

# 4. 検索エンジンを実行
cd cypher/kuzu && bash ../../run_with_kuzu.sh uv run python main.py
```

## 各検索エンジンの実行

### Cypher（グラフ検索）
```bash
cd cypher/kuzu
bash ../../run_with_kuzu.sh uv run python main.py
```

### FTS（全文検索）
```bash
cd fts/kuzu
bash ../../run_with_kuzu.sh uv run python main.py
```

### VSS（ベクトル検索）
```bash
cd vss/kuzu
bash ../../run_with_kuzu.sh uv run python main.py
```

## トラブルシューティング

### Q: libstdc++.so.6エラーが出る
A: `run_with_kuzu.sh`を使用してください。直接実行する場合:
```bash
export LD_LIBRARY_PATH=/nix/store/4gk773fqcsv4fh2rfkhs9bgfih86fdq8-gcc-13.3.0-lib/lib
uv run python main.py
```

### Q: "Table Document does not exist"エラー
A: データベースを初期化してください:
```bash
cd /home/nixos/bin/src/data/kuzu
python setup.py
```

### Q: ImportError: No module named 'db'
A: 正しいディレクトリから実行してください。各検索エンジンのディレクトリ内で実行する必要があります。