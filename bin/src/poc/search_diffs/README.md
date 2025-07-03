# search_diffs

ディレクトリリストの差分を検出して差分情報を出力

## 責務
**前回と今回のディレクトリリスト → 追加/削除されたパスの差分情報**

## 使用例
```bash
# 初回実行（すべて追加として出力）
find . -type d | nix develop -c search_diffs

# 2回目以降（差分のみ出力）
find . -type d | nix develop -c search_diffs --state-file=.dirstate
```

## 入力
```
src
src/main
src/utils
```

## 出力
```
+ src/new_module
- src/old_module
= src/main
```

## 状態ファイル
前回のディレクトリリストを`.dirstate`に保存して差分検出に使用