-- vim.opt.completeopt=menu,menuone,noselect 

local cmp = require("cmp")
local lspkind = require("lspkind")
local devicons = require('nvim-web-devicons')

cmp.setup({
  -- enabled = function()
  --   local context = require("cmp.config.context")
  --   if vim.api.nvim_get_mode().mode == 'c' then
  --     return true
  --   else
  --     return not context.in_syntax_group("Comment")
  --     -- https://github.com/hrsh7th/nvim-cmp/wiki/Advanced-techniques
  --     --  and nocontext.in_treesitter_captre("comment")
  --   end
  --
  --   local cmp_autopairs = require('nvim-autopairs.completion.cmp')
  --   cmp.event:on(
  --     'confirm_done',
  --     cmp_autopairs.on_confirm_done()
  --   )
  -- end,
  style = {
    winhighlight = "NormalFloat:NormalFloat,FloatBorder:FloatBorder",
  },
  formatting = {
    -- if you don't define "lspkind.lua" file...
    -- fields = {"kind", "abbr", "menu"},
    -- format = function(entry, vim_item)
    --   vim_item.menu_hl_group = "CmpItemKind" .. vim_item.kind
    --    vim_item.menu = vim_item.kind
    --    vim_item.abbr = vim_item.abbr:sub(1, 50)
    --    -- vim_item.kind = '[' .. symbols[vim_item.kind] .. ']'
    --   return vim_item
    -- end
    -- format = lspkind.cmp_format({
    --   mode = "symbol_text",
    --   menu = ({
    --     buffer = "[Buffer]",
    --     nvim_lsp = "[LSP]",
    --     luasnip = "[LuaSnip]",
    --     nvim_lua = "[Lua]",
    --     latex_symbols = "[Latex]",
    --   }),
    --   with_text = false,
    --   maxwidth = 50,
    -- }),
    format = function(entry, vim_item)
     if vim.tbl_contains({ 'path' }, entry.source.name) then
       local icon, hl_group = require('nvim-web-devicons').get_icon(entry:get_completion_item().label)
       if icon then
         vim_item.kind = icon
         vim_item.kind_hl_group = hl_group
         return vim_item
       end
     end
     return lspkind.cmp_format({ with_text = false })(entry, vim_item)
    end
  },
  experimental = {
    native_menu = false,
    ghost_text = true,
  },
  window = {
    -- completion = cmp.config.window.bordered(),
    -- documentation = cmp.config.window.bordered(),
    completion = {
      border = { "╭", "─", "╮", "│", "╯", "─", "╰", "│" },
      scrollbar = "║",
      winhighlight = 'Normal:CmpMenu,FloatBorder:CmpMenuBorder,CursorLine:CmpSelection,Search:None',
      autocomplete = {
        require("cmp.types").cmp.TriggerEvent.InsertEnter,
        require("cmp.types").cmp.TriggerEvent.TextChanged,
      },
    },
    documentation = {
      border = { "╭", "─", "╮", "│", "╯", "─", "╰", "│" },
      winhighlight = "NormalFloat:NormalFloat,FloatBorder:FloatBorder",
      scrollbar = "║",
    },
  },
  view = {
    entries = "native"
  },
  sorting = {
    --keep priority weight at 2 for much closer matches to appear above copilot
    --set to 1 to make copilot always appear on top
    priority_weight = 1,
    comparators = {
      -- order matters here
      cmp.config.compare.exact,
      has_copilot and copilot_cmp.prioritize or nil,
      has_copilot and copilot_cmp.score or nil,
      cmp.config.compare.offset,
      -- cmp.config.compare.scopes, --this is commented in nvim-cmp too
      cmp.config.compare.score,
      cmp.config.compare.recently_used,
      cmp.config.compare.locality,
      cmp.config.compare.kind,
      cmp.config.compare.sort_text,
      cmp.config.compare.length,
      cmp.config.compare.order,
      -- personal settings:
      -- cmp.config.compare.recently_used,
      -- cmp.config.compare.offset,
      -- cmp.config.compare.score,
      -- cmp.config.compare.sort_text,
      -- cmp.config.compare.length,
      -- cmp.config.compare.order,
    },
  },
  -- snippet = {
  --   -- REQUIRED - you must specify a snippet engine
  --   expand = function(args)
  --     -- vim.fn["vsnip#anonymous"](args.body) -- For `vsnip` users.
  --     -- require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
  --     -- require('snippy').expand_snippet(args.body) -- For `snippy` users.
  --     -- vim.fn["UltiSnips#Anon"](args.body) -- For `ultisnips` users.
  --   end,
  -- },
  sources = {
    { name = "nvim_lsp" },
    { name = "luasnip" },
    { name = "vsnip" },
    { name = "path" },
    { name = "cmp_tabnine" },
    { name = "skkeleton" },
    { name = "copilot", group_index = 2 },
  }, {
    -- { name = "buffer" , option = { keyword_pattern = [[\k\+]], }},
    -- { name = "cmdline" },
  },
  mapping = {
    ["<C-p>"] = cmp.mapping.select_prev_item(),
    ["<C-n>"] = cmp.mapping.select_next_item(),
    ["<C-d>"] = cmp.mapping(cmp.mapping.scroll_docs(-4), { "i", "c" }),
    ["<C-u>"] = cmp.mapping(cmp.mapping.scroll_docs(4), { "i", "c" }),
    ["<C-l>"] = cmp.mapping.complete(),
    ["<C-e>"] = cmp.mapping.abort(),
    ["<CR>"] = cmp.mapping.confirm({ select = false }),
    ["<C-CR>"] = cmp.mapping.confirm({ select = true }),
--      ["<UP>"] = cmp.mapping.select_prev_item({ behavior = cmp.SelectBehavior }),
--      ["<DOWN>"] = cmp.mapping.select_next_item({ behavior = cmp.SelectBehavior })
  },
  preselect = cmp.PreselectMode.Item,
})

-- --set max height of items
-- vim.cmd([[ set pumheight=6 ]])
-- --set highlights
-- local highlights = {
--   -- type highlights
--   CmpItemKindText = { fg = "LightGrey" },
--   CmpItemKindFunction = { fg = "#C586C0" },
--   CmpItemKindClass = { fg = "Orange" },
--   CmpItemKindKeyword = { fg = "#f90c71" },
--   CmpItemKindSnippet = { fg = "#565c64" },
--   CmpItemKindConstructor = { fg = "#ae43f0" },
--   CmpItemKindVariable = { fg = "#9CDCFE", bg = "NONE" },
--   CmpItemKindInterface = { fg = "#f90c71", bg = "NONE" },
--   CmpItemKindFolder = { fg = "#2986cc" },
--   CmpItemKindReference = { fg = "#922b21" },
--   CmpItemKindMethod = { fg = "#C586C0" },
--   CmpItemKindCopilot = { fg = "#6CC644" },
--   -- CmpItemMenu = { fg = "#C586C0", bg = "#C586C0" },
--   CmpItemAbbr = { fg = "#565c64", bg = "NONE" },
--   CmpItemAbbrMatch = { fg = "#569CD6", bg = "NONE" },
--   CmpItemAbbrMatchFuzzy = { fg = "#569CD6", bg = "NONE" },
--   CmpMenuBorder = { fg="#263341" },
--   CmpMenu = { bg="#10171f" },
--   CmpSelection = { bg="#263341" },
-- }
--
-- for group, hl in pairs(highlights) do
--   vim.api.nvim_set_hl(0, group, hl)
-- end

-- https://www.reddit.com/r/neovim/comments/wscfar/how_to_get_bordered_ui_for_hover_actions_in/
-- https://neovim.discourse.group/t/make-nvim-cmp-show-full-function-help-again-instead-of-signature-only/1863/4

-- https://zenn.dev/takuya/articles/4472285edbc132 ,  https://zenn.dev/botamotch/articles/21073d78bc68bf
-- vim.cmd [[
--   set completeopt=menuone,noinsert,noselect
--   highlight! default link CmpItemKind CmpItemMenuDefault
--   set updatetime=500
--   highlight LspReferenceText  cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040
--   highlight LspReferenceRead  cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040
--   highlight LspReferenceWrite cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040
-- vim.cmd [[
--   augroup lsp_document_highlight
--     autocmd!
--     autocmd CursorHold,CursorHoldI * lua vim.lsp.buf.document_highlight()
--     autocmd CursorMoved,CursorMovedI * lua vim.lsp.buf.clear_references()
--   augroup END
-- ]]
-- 

cmp.setup.filetype("gitcommit", {
  sources = cmp.config.sources({
    { name = "cmp_git" }, -- You can specify the `cmp_git` source if you were installed it.
  }, {
    { name = "buffer" },
  })
})

cmp.register_source('devicons', {
  complete = function(self, params, callback)
    local items = {}
    for _, icon in pairs(devicons.get_icons()) do
      table.insert(items, {
        label = icon.icon .. '  ' .. icon.name,
        insertText = icon.icon,
        filterText = icon.name,
      })
    end
    callback({ items = items })
  end,
})

require("copilot_cmp").setup {
  method = "getCompletionsCycling",
  formatters = {
    label = require("copilot_cmp.format").format_label_text,
    insert_text = require("copilot_cmp.format").format_insert_text,
    preview = require("copilot_cmp.format").deindent,
  },
}
-- https://github.com/zbirenbaum/copilot.lua#suggestion
-- cmp.event:on("menu_closed", function()
--   vim.b.copilot_suggestion_hidden = false
-- end)

-- cmp.setup.cmdline('/', {
--   mapping = cmp.mapping.preset.cmdline(),
--   sources = {
--     { name = 'buffer' }
--   }
-- })

-- cmp.setup.cmdline(':', {
--   mapping = cmp.mapping.preset.cmdline(),
--   sources = cmp.config.sources({
--     { name = 'path' }
--   }, {
--     {
--       name = 'cmdline',
--       option = {
--         ignore_cmds = { 'Man', '!' }
--       }
--     }
--   })
-- })
--
-- emmet_ls = function() 
--   local lspconfig = require('lspconfig')
--   local configs = require('lspconfig/configs')
--   local capabilities = vim.lsp.protocol.make_client_capabilities()
--   capabilities.textDocument.completion.completionItem.snippetSupport = true
--
--   lspconfig.emmet_ls.setup({
--       -- on_attach = on_attach,
--       capabilities = capabilities,
--       filetypes = { 'html', 'typescriptreact', 'javascriptreact', 'css', 'sass', 'scss', 'less' },
--       init_options = {
--         html = {
--           options = {
--             -- For possible options, see: https://github.com/emmetio/emmet/blob/master/src/config.ts#L79-L267
--             ["bem.enabled"] = true,
--           },
--         },
--       }
--   })
-- end
-- emmet_ls()
