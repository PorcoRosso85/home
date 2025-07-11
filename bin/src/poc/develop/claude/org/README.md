# Claude Organization Templates

## 概要

並列Claude実行のためのテンプレート集。直接実行やsourceは禁止。

## 使用方法

### 1. テンプレートを参照
```bash
cat ~/bin/src/poc/develop/claude/org/main.sh.template
```

### 2. 自分のスクリプトを作成
```bash
#!/bin/bash
# my_parallel_task.sh

# パラメータを設定
TASKS=(
  "auth-feature:src/auth:認証機能を実装:development"
  "api-design:docs/api:API設計書を作成:readonly"
)

# worktree作成関数（テンプレートから複製）
create_sparse_worktree() {
  # ... テンプレートの実装を複製 ...
}

# 実行
for task in "${TASKS[@]}"; do
  IFS=':' read -r name dir prompt mode <<< "$task"
  WORKTREE=$(create_sparse_worktree "$name" "$dir")
  # ... Claude起動処理 ...
done
```

### 3. 実行
```bash
bash my_parallel_task.sh
```

## なぜテンプレート？

- **カスタマイズ強制**: 各ユーザーが自分のニーズに合わせて実装
- **パラメータ明示化**: ハードコードされた値を避け、明示的な設定を促進
- **安全性**: 誤った実行を防止

## ファイル構成

- `main.sh.template`: メインテンプレート（実行不可）
- `README.md`: このファイル