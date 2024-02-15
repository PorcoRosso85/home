vim.cmd([[
  let test#strategy = {
    \ 'nearest': 'neovim',
    \ 'file':    'dispatch',
    \ 'suite':   'basic',
  \}
]])

-- https://shase428.hatenablog.jp/entry/2021/02/18/001632
vim.cmd([[
  let g:test#strategy = 'neoterm'
  let g:neoterm_default_mod='belowright'
  let g:neoterm_size=10
  let g:neoterm_autoscroll=1
  let g:neoterm_shell = '$SHELL -l'

  let g:test#preserve_screen = 1
  let g:test#python#runner = 'pytest'
  let g:test#python#pytest#executable = $VIRTUAL_ENV
]])

