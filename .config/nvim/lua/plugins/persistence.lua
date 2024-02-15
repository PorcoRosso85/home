local utils = require("utils._set_mappings")
require("persistence").setup{
  dir = vim.fn.expand(vim.fn.stdpath("config") .. "/sessions/"), -- directory where session files are saved
  --options = { "buffers" },
  options = { "buffers", "curdir", "tabpages", "winsize" }, -- sessionoptions used for saving
}
utils.nnoremap("<leader>ql", "<cmd>lua require('persistence').load({ last = true })<cr>")
