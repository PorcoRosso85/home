require("debugprint").setup({
  opts = {
    create_keymaps = false,
    create_commands = false,
  },
})

-- vim.api.nvim_create_user_command("DeleteDebugPrints", function(opts)
--     -- Note: you must set `range=true` and pass through opts for ranges to work
--     M.deleteprints(opts)
-- end, {
--     range = true})
-- end)
