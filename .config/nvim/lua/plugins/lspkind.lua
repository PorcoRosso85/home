require('lspkind').init({
    -- DEPRECATED (use mode instead): enables text annotations
    --
    -- default: true
    -- with_text = true,

    -- defines how annotations are shown
    -- default: symbol
    -- options: 'text', 'text_symbol', 'symbol_text', 'symbol'
    mode = 'symbol_text',

    -- default symbol map
    -- can be either 'default' (requires nerd-fonts font) or
    -- 'codicons' for codicon preset (requires vscode-codicons font)
    --
    -- default: 'default'
    preset = 'default',

    -- override preset symbols
    --
    -- default: {}
    symbol_map = {
      Text = "",
      Method = "",
      Function = "",
      Constructor = "",
      Field = "ﰠ",
      Variable = "",
      Class = "ﴯ",
      Interface = "",
      Module = "",
      Property = "ﰠ",
      Unit = "塞",
      Value = "",
      Enum = "",
      Keyword = "",
      Snippet = "",
      Color = "",
      File = "",
      Reference = "",
      Folder = "",
      EnumMember = "",
      Constant = "",
      Struct = "פּ",
      Event = "",
      Operator = "",
      TypeParameter = "",
      Copilot = "",
    },

    menu = ({
      buffer = "[Buffer]",
      nvim_lsp = "[LSP]",
      luasnip = "[LuaSnip]",
      nvim_lua = "[Lua]",
      latex_symbols = "[Latex]",
    }),
})

vim.api.nvim_set_hl(0, "CmpItemKindCopilot", {fg ="#6CC644"})


-- cmp.lua
--
--  formatting = {
--    -- if you don't define "lspkind.lua" file...
--    --format = lspkind.cmp_format({
--    --  mode = "symbol_text",
--    --  menu = ({
--    --    buffer = "[Buffer]",
--    --    nvim_lsp = "[LSP]",
--    --    luasnip = "[LuaSnip]",
--    --    nvim_lua = "[Lua]",
--    --    latex_symbols = "[Latex]",
--    --  })
--    --}),
--  --  format = function(entry, vim_item)
--  --    if vim.tbl_contains({ 'path' }, entry.source.name) then
--  --      local icon, hl_group = require('nvim-web-devicons').get_icon(entry:get_completion_item().label)
--  --      if icon then
--  --        vim_item.kind = icon
--  --        vim_item.kind_hl_group = hl_group
--  --        return vim_item
--  --      end
--  --    end
--  --    return lspkind.cmp_format({ with_text = false })(entry, vim_item)
--  --  end
--  },
