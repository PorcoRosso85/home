# add-command
/add-command

# 説明
新しいカスタムコマンドを追加して、CLAUDE.mdに登録する

# 実行内容
1. コマンド名を確認する（例: /my-command）
2. ~/.claude/commands/コマンド名.mdファイルを作成
3. コマンドの説明と実行内容を記載
4. CLAUDE.mdの「作業の合言葉」セクションに自然言語マッピングを追加
5. 必要に応じてコマンドの使用例を表示

# ディレクトリ構造
```
~/.claude/
├── commands/      # コマンド定義ファイル（.md）
├── scripts/       # コマンドから使用されるスクリプト（.sh, .py等）
├── *.sql          # SQLファイル（ddl.sql, dml.sql, dql.sql等）
└── coordination.db # データベースファイル
```

# ルール
- コマンド定義は `~/.claude/commands/` に配置
- 実行スクリプトは `~/.claude/scripts/` に配置
- スクリプトファイル名は `コマンド名_用途.sh` の形式を推奨

# テンプレート
```markdown
# コマンド名
/新しいコマンド

# 説明
このコマンドの目的と機能

# 実行内容
1. 実行する手順1
2. 実行する手順2
3. 実行する手順3

# 関連スクリプト（ある場合）
- ~/.claude/scripts/コマンド名_main.sh
```