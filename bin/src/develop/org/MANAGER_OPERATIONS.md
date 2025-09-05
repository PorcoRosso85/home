# Manager操作ガイド（Orchestrator用）

## ✅ 正しい操作方法

### Manager起動
```python
from application import start_manager
result = start_manager('x')  # または 'y', 'z'
```

### Manager へのコマンド送信
```python
from application import send_command_to_manager
result = send_command_to_manager('x', 'instructions.mdを確認してください')
```

### Worker起動（任意ディレクトリ）
```python
from application import start_worker
result = start_worker('/path/to/project')
```

## ❌ 避けるべき操作

1. **手動tmuxコマンド**
   - `tmux split-window` → `start_manager()`を使用
   - `tmux send-keys -t 0.2` → `send_command_to_manager()`を使用
   - pane番号の推測は絶対にしない

2. **pane番号の決め打ち**
   - `%0`, `%1`, `%2`などの固定番号を想定しない
   - tmuxは動的にpane IDを割り当てる（%51など）

3. **直接Claude起動**
   - `tmux send-keys "claude"` → `start_manager()`に含まれる

## 原則

**「tmuxコマンドを直接使わない」**
- すべての操作はapplication.py経由
- pane管理はapplication.pyに委譲
- エラーハンドリングも自動化

## デバッグ用コマンド

状況確認のみに使用：
```bash
# pane一覧確認
tmux list-panes -F "#{pane_id} #{pane_current_path}"

# Manager状態確認
from application import get_all_workers_status
print(get_all_workers_status())
```