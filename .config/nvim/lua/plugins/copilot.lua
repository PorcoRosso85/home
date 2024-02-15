local utils = require("utils._set_mappings")

require('copilot').setup({
  panel = {
    enabled = false,
    auto_refresh = false,
    keymap = {
      jump_prev = "[[",
      jump_next = "]]",
      accept = "<M-CR>",
      refresh = "gr",
      open = "<M-CR>"
    },
  },
  suggestion = {
    enabled = true,
    auto_trigger = false,
    debounce = 150,
    keymap = {
      accept = "<M-CR>",
      accept_word = false,
      accept_line = false,
      next = "<M-]>",
      prev = "<M-[>",
      dismiss = "<C-]>",
    },
  },
  filetypes = {
    yaml = true,
    markdown = true,
    help = false,
    gitcommit = false,
    gitrebase = false,
    hgcommit = false,
    svn = false,
    cvs = false,
    ["."] = false, -- e.g. .dots, .env
    terraform = true,
    -- ["*"] = false, -- disable for all other filetypes and ignore default `filetypes`
  },
  copilot_node_command = 'node', -- Node.js version must be > 16.x
  -- server_opts_overrides = {
  --   trace = "verbose",
  --   settings = {
  --     advanced = {
  --       listCount = 10, -- #completions for panel
  --       inlineSuggestCount = 3, -- #completions for getCompletions
  --     }
  --   },
  -- }
})


-- utils.nnoremap("<C-j>copilotpanelnext", '<cmd>lua require("copilot.panel").jump_next()<cr>')
-- utils.nnoremap("<C-j>copilotpanelprev", '<cmd>lua require("copilot.panel").jump_prev()<cr>')
vim.api.nvim_create_user_command("CopilotPanelOpen", 'lua require("copilot.panel").open()', {})

vim.api.nvim_create_user_command("CopilotSuggestionVisible", 'lua require("copilot.suggestion").is_visible()', {})
utils.nnoremap("<C-j>copilotsuggestiontoggleauto", '<cmd>lua require("copilot.suggestion").toggle_auto_trigger()<cr>')
