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
    -- Ctrl+b をプレフィックスキーとして設定
    { key = 'b', mods = 'CTRL', action = wezterm.action.SetKeyTable({name = 'tmux'}) },
  },

  key_tables = {
    tmux = {
      { key = '%', action = wezterm.action.SplitHorizontal() },
      { key = '"', action = wezterm.action.SplitVertical() }, -- 垂直分割も同様に設定する場合
      { key = 'c', action = wezterm.action.SpawnTab('CurrentPaneDomain') }, -- 新しいタブを同様に設定する場合
      { key = 'n', action = wezterm.action.ActivateTabRelative(1) }, -- 次のタブ
      { key = 'p', action = wezterm.action.ActivateTabRelative(-1) }, -- 前のタブ
      { key = ' ', action = wezterm.action.TogglePaneZoomState() }, -- pane zoom
      { key = 'x', action = wezterm.action.CloseCurrentPane() }, -- pane を閉じる
      { key = 'd', action = wezterm.action.Detach() }, -- detach
      { key = '?', action = wezterm.action.ShowLauncherArgs() }, -- ヘルプを表示
      { key = ':', action = wezterm.action.ActivateCommandPalette() }, -- コマンドパレット
      -- 必要に応じて tmux の他のキーバインドもここに追加できます
    },
  },

  -- その他のWezTerm設定 (必要に応じて追記)
}
