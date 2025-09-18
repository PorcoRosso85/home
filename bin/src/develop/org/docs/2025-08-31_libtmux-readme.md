---
url: https://github.com/tmux-python/libtmux
saved_at: 2025-08-31T17:00:00Z
title: libtmux - Python wrapper for tmux
domain: github.com
---

# libtmux

libtmux is a typed Python library that provides a wrapper for interacting programmatically with tmux, a terminal multiplexer.

## Installation

```bash
pip install --user libtmux
```

## Core Capabilities

- Manage tmux servers, sessions, windows, and panes
- Powers tmuxp (tmux workspace manager)
- Supports tmux 1.8+ and Python 3.9+

## Key Usage Examples

```python
import libtmux

# Connect to tmux server
server = libtmux.Server()

# Create a new session
session = server.new_session(session_name='my_project')

# Create a new window
window = session.new_window(window_name='development')

# Split window into panes
pane = window.split()

# Send keystrokes to a pane
pane.send_keys('echo "Hello, tmux!"')
```

## Project Details

- Open Source (MIT License)
- Documentation: https://libtmux.git-pull.com
- GitHub: https://github.com/tmux-python/libtmux

The library allows developers to programmatically control and interact with tmux sessions using a Pythonic interface.