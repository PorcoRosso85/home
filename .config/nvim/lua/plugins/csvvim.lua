--vim.cmd[[ setfiletype csv ]]
vim.cmd([[
  let g:csv_comment = '#'
  let g:csv_delim = ','
  let g:csv_highlight_column = 'y'
  let g:csv_hiHeader = 'Pmenu'
  let g:csv_hiGroup = "IncSearch"
  let g:csv_autocmd_arrange	= 1
  let g:csv_autocmd_arrange_size = 1024*1024
]])
--vim.cmd[[ filetype plugin on ]]
--
--vim.cmd([[
--  if exists("did_load_csvfiletype")
--    finish
--  endif
--  let did_load_csvfiletype=1
--
--  augroup filetypedetect
--    au! BufRead,BufNewFile *.csv,*.dat	setfiletype csv
--  augroup END
--]])

-- filetype
-- https://zenn.dev/rapan931/articles/45b09b774512fc
-- https://vi.stackexchange.com/questions/27897/how-to-get-the-filetype-in-lua-in-nvim
