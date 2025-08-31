#!/usr/bin/env python3
"""
Transport Module Configuration Variables
全ての設定値を一元管理
"""

from pathlib import Path
from typing import Dict, Any

# パス設定
PATHS: Dict[str, Path] = {
    "base_dir": Path("/home/nixos/bin/src/poc/realtime-claudecode"),
    "claude_shell": Path("/home/nixos/bin/src/develop/claude/ui/claude-shell.sh"),
    "claude_projects": Path.home() / ".claude" / "projects"
}

# タイムアウト設定（秒）
TIMEOUTS: Dict[str, int] = {
    "default": 30,
    "jsonl_wait": 30,
    "startup": 30,
    "command": 10
}

# PTY設定
PTY_CONFIG: Dict[str, Any] = {
    "encoding": "utf-8",
    "dimensions": (24, 80)
}

# tmux設定
TMUX_CONFIG: Dict[str, str] = {
    "default_window": "1",
    "pane_format": "{window}.{pane}"
}

# プロンプトパターン（正規表現）
PROMPT_PATTERNS: list = [
    "Welcome",
    r">\s*│",
    "Starting Claude",
    r"cwd:"
]

# 設定値のみ、関数はdomain.pyに移動