# Claude Code Transport Module

複数Claude Codeインスタンスの管理・通信基盤

## 概要

- **目的**: Claude Code並列実行によるタスク分散
- **実装**: pexpectによるセッション管理（tmux非依存）
- **制約**: 1ディレクトリ1セッション（プロセス検出で保証）

## 使い方

```bash
# 全コマンド例を表示（コピペ実行可能）
cat cli.sh.example

# 最小例: セッション一覧
nix shell --impure --expr '(import <nixpkgs> {}).python312.withPackages (ps: [ps.pexpect])' \
  -c python3 -c "
from application import MultiSessionOrchestrator
print(MultiSessionOrchestrator().discover_active_sessions()['sessions'])
"
```

## アーキテクチャ

```
application.py     # 実質エントリーポイント（API）
├── infrastructure.py # pexpectセッション管理
└── domain.py        # ドメインモデル
```

## API使用例

```python
from infrastructure import create_session, list_sessions
from pathlib import Path

# セッション作成
session = create_session(Path("/path/to/work"))

# セッション一覧
sessions = list_sessions()
```

## 制約

- **1ディレクトリ1セッション**: プロセス検出で重複防止
- **pexpect必須**: `nix shell --impure --expr '...'`で導入

## トラブルシューティング

### pexpectエラー
```bash
# NG: 分離パッケージ
nix shell nixpkgs#python312 nixpkgs#python312Packages.pexpect

# OK: withPackages統合
nix shell --impure --expr '(import <nixpkgs> {}).python312.withPackages (ps: [ps.pexpect])'
```

## 参照

- [cli.sh.example](./cli.sh.example) - 実行可能な全コマンド例