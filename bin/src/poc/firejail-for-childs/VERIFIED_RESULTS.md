# 実証済み：Claude Codeの子ディレクトリアクセス制限

## 実際のテスト結果

### 1. Firejailアプローチ - **失敗**
```bash
firejail --blacklist=$(pwd)/test-dirs/child1 -- claude
```
**結果**: `Error ../../src/firejail/util.c:1041: create_empty_dir_as_root: mkdir: Permission denied`
- NixOSでfirejailはroot権限が必要
- 通常ユーザーでは動作不可

### 2. ファイルシステム権限アプローチ - **成功** ✅

#### 実行したテスト
```bash
# 権限を000に設定
chmod 000 test-dirs/child1 test-dirs/child2 test-dirs/child3
```

#### Claude Codeでの実際のエラー

1. **書き込み試行時**:
```
● Write(test-dirs/child1/newfile.txt)
  ⎿  Error: EACCES: permission denied, open '/home/nixos/bin/src/poc/firejail-for-childs/test-dirs/child1/newfile.txt'
```

2. **読み取り試行時**:
```
● Read(test-dirs/child1/secret.txt)
  ⎿  Error reading file
```

## 結論

### 有効な制限方法
1. **ファイルシステム権限（chmod）** - 実証済み、動作確認済み
   - 簡単に実装可能
   - Claude Codeは権限エラーを正しく受け取る
   - root権限不要

2. **CLAUDE.md規約** - 実装済み、運用中
   - 自己制御に依存
   - 柔軟性が高い

3. **Hooks検証** - 部分実装済み
   - 編集前にチェック可能
   - カスタマイズ可能

### 無効な方法
1. **Firejail** - NixOSでは実用不可
   - root権限が必要
   - Claude Codeの起動方法（nix run）と相性が悪い

## 推奨実装

```bash
# 保護したいディレクトリの権限を制限
chmod 700 sensitive-data/  # オーナーのみアクセス可
chmod 000 do-not-touch/    # 完全にブロック

# Claude起動
claude  # 制限されたディレクトリにはアクセスできない
```

この方法が最もシンプルで確実です。