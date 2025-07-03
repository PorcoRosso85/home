# build_diffs

差分情報からKuzuDBの検索インデックスを更新

## 責務
**ディレクトリの追加/削除情報 → KuzuDBインデックスの差分更新**

## 使用例
```bash
# 差分を適用してDBを更新
echo -e "+ src/new\n- src/old" | nix develop -c build_diffs

# 初期構築（全追加として処理）
find . -type d | nix develop -c build_diffs --init

# パイプライン例
find . -type d | search_diffs | build_diffs
```

## 入力
```
+ src/new_module
- src/old_module
```

## 出力
```
Added: 1 directories
Deleted: 1 directories
Updated index in 0.05s
```

## データベース
KuzuDBを使用してディレクトリ情報とREADMEコンテンツをインデックス化