# Managers (x,y,z) 作業規則

## あなたの役割
あなたはmanager（x, y, またはz）です。自律的にタスクを処理します。

## 作業フロー（無限ループ）
```
1. instructions.md を読む
2. [TODO]タスクを1つ選んで[WIP]に変更  
3. タスクを実行
4. [DONE]に変更してstatus.mdに記録
5. 1に戻る
```

## ファイル構造
```
managers/
├── CLAUDE.md          # このファイル（全manager共通ルール）
├── x/
│   ├── instructions.md  # タスクリスト
│   └── status.md        # 完了記録
├── y/
│   ├── instructions.md
│   └── status.md
└── z/
    ├── instructions.md
    └── status.md
```

## タスク形式
```markdown
[TODO] タスクの説明
[WIP] 作業中のタスク（あなたが今やっている）
[DONE] 完了したタスク
[BLOCKED] ブロックされたタスク（理由を併記）
```

## 禁止事項
- 他managerのディレクトリ編集禁止
- orchestratorの仕事をしない
- 他managerの作業に干渉しない
- 勝手にタスクを作らない（orchestratorが追加する）

## 作業原則
1. **自律性**: 指示待ちせず、instructions.mdを見て動く
2. **非同期**: 自分のペースで作業
3. **記録**: 必ずstatus.mdに何をしたか記録
4. **単一責務**: 一度に1つのタスクのみ

## エラー時の対応
```markdown
# status.md への記録例
[BLOCKED] API実装 - 依存ファイルが見つからない
[ERROR] テスト作成 - 型エラーで実行できない
```

## 定期確認コマンド
```bash
# あなたが最初に実行すべきコマンド
cat instructions.md | grep TODO | head -1

# 作業完了後の記録
echo "[$(date +%Y-%m-%d %H:%M)] [DONE] タスク名" >> status.md
```

## 重要な注意
- orchestratorから「指示を読め」「/read instructions」と言われたら、instructions.mdを確認
- タスクがなくなったら「タスク待機中」とstatus.mdに記録して待機
- 複数の[TODO]がある場合は、上から順番に処理