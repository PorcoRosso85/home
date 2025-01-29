local wezterm = require 'wezterm'

return {
  -- デフォルトの起動コマンドを設定します。
  default_prog = { 'wsl.exe', '-d', 'nix' },

  -- (オプション) デフォルトのドメイン名を 'WSL' に設定 (必須ではないですが、わかりやすくなります)
  default_domain = 'WSL',

  keys = {
    {
      key = "h",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Left"),
    },
    {
      key = "j",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Down"),
    },
    {
      key = "k",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Up"),
    },
    {
      key = "l",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Right"),
    },
    {
      key = "LeftArrow",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Left"),
    },
    {
      key = "DownArrow",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Down"),
    },
    {
      key = "UpArrow",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Up"),
    },
    {
      key = "RightArrow",
      mods = "CTRL",
      action = wezterm.action.ActivatePaneDirection("Right"),
    },
  },

  -- その他のWezTerm設定 (必要に応じて追記)
}
