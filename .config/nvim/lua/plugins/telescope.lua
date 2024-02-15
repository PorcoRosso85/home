local utils = require("utils._set_mappings")
-- local builtin = require("telescope.builtin")
-- local key = vim.keymap.set
-- require('telescope').load_extension('media_files')

require('telescope').setup {
  defaults = {
    mappings = {},
  },
  pickers = {
  },
  extensions = {
    media_files = {
      -- filetypes whitelist
      -- defaults to {"png", "jpg", "mp4", "webm", "pdf"}
      filetypes = {"png", "webp", "jpg", "jpeg"},
      find_cmd = "rg" -- find command (defaults to `fd`)
    }
  },
}


-- utils.nnoremap("<leader>tlf", "<cmd>lua require('telescope.builtin').find_files({layout_config={width=0.9}})<cr>")
-- key('n', '<leader>tlh', builtin.help_tags, {})
-- key('n', '<leader>tlg', builtin.live_grep, {})
-- key('n', '<leader>tlq', builtin.quickfix, {})
-- key('n', '<leader>tll', builtin.loclist, {})
-- key('n', '<leader>tlj', builtin.jumplist, {})
-- key('n', '<leader>tlgs', builtin.git_status, {})
--
-- key('n', '<leader>tlpp', builtin.planets, {})
-- key('n', '<leader>tlpb', builtin.builtin, {})
