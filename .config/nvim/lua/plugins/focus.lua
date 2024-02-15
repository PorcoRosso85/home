local utils = require("utils._set_mappings")

require("focus").setup({
  --colorcolumn = {
  --  enable = true,
  --  width = 100
  --},
  winhighlight = false,
  number = false,
  hybridnumber = true,
})

--utils.nnoremap("<leader>wn", ":FocusSplitNicely<cr>")
--
-- vim.cmd("hi link UnfocusedWindow Normal")
-- vim.cmd("hi link FocusedWindow Normal")
