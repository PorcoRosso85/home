local utils = require("utils._set_mappings")
-- -- prefix = utils.prefix + q key
-- local prefix = utils.prefix .. "q"
local prefix = "<C-j>q"
-- -- Run the nearest test
utils.nnoremap('<prefix>..q', '<cmd>require("neotest").run.run()<cr>')
--
-- -- Run the current file
-- require("neotest").run.run(vim.fn.expand("%"))
--
-- -- Debug the nearest test (requires nvim-dap and adapter support)
-- require("neotest").run.run({strategy = "dap"})
--


require("neotest").setup({
  adapters = {
    -- require("neotest-python")({
    --   dap = { justMyCode = false },
    -- }),
    -- require("neotest-plenary"),
    -- require("neotest-vim-test")({
    --   ignore_file_types = { "python", "vim", "lua" },
    --   allow_file_types = { "haskell", "elixir" }
    -- }),
  },
})


