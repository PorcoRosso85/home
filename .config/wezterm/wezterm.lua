local wezterm = require 'wezterm'

return {
  -- デフォルトの起動コマンドを設定します。
  default_prog = { 'wsl.exe', '-d', 'nix' },

  -- (オプション) デフォルトのドメイン名を 'WSL' に設定 (必須ではないですが、わかりやすくなります)
  default_domain = 'WSL',

  -- その他のWezTerm設定 (必要に応じて追記)
}
