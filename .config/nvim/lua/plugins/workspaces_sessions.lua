local utils = require("utils._set_mappings")
local workspaces = require("workspaces")
--local sessions = require("sessions")

workspaces.setup({
  path = vim.fn.stdpath("data").. "/workspaces",
  --hooks = {
  --  open = {
  --    --lua command like "Telescope find_files"
  --    function() require("sessions").load(nil, { silent = true }) end,
  --  }
  --}
})
utils.nnoremap("<leader>wsa", "<cmd>WorkspacesAdd<cr>")
utils.nnoremap("<leader>wsr", "<cmd>WorkspacesRemove<cr>")
utils.nnoremap("<leader>wso", "<cmd>WorkspacesOpen<cr>")

--sessions.setup({
--    events = { "WinEnter", "VimLeavePre", "ToggleTerm" },
--    --session_filepath = vim.fn.stdpath("data").. "/sessions/",
--    session_filepath = vim.fn.stdpath("data").. "/sessions",
--})
--utils.nnoremap("<leader>wss", "<cmd>SessionsSave<cr>")
--utils.nnoremap("<leader>wsl", "<cmd>SessionsLoad<cr>")
