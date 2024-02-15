-- LSP handlers
vim.lsp.handlers["textDocument/publishDiagnostics"] = vim.lsp.with(
  vim.lsp.diagnostic.on_publish_diagnostics, { virtual_text = false }
)

-- vim.cmd("set updatetime=500")
-- vim.cmd("highlight LspReferenceText  cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040")
-- vim.cmd("highlight LspReferenceRead  cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040")
-- vim.cmd("highlight LspReferenceWrite cterm=underline ctermfg=1 ctermbg=8 gui=underline guifg=#A00000 guibg=#104040")
-- vim.cmd("augroup lsp_document_highlight")
-- vim.cmd("  autocmd!")
-- vim.cmd("  autocmd CursorHold,CursorHoldI * lua vim.lsp.buf.document_highlight()")
-- vim.cmd("  autocmd CursorMoved,CursorMovedI * lua vim.lsp.buf.clear_references()")
-- vim.cmd("augroup END")
local function on_attach(client, bufnr)
    -- Find the clients capabilities
    local cap = client.resolved_capabilities

    -- Only highlight if compatible with the language
    if cap.document_highlight then
        vim.cmd('augroup LspHighlight')
        vim.cmd('autocmd!')
        vim.cmd('autocmd CursorHold <buffer> lua vim.lsp.buf.document_highlight()')
        vim.cmd('autocmd CursorMoved <buffer> lua vim.lsp.buf.clear_references()')
        vim.cmd('augroup END')
    end
end

local utils = require("utils._set_mappings")
local lspconfig = require("lspconfig")
local cmp = require("cmp_nvim_lsp")
local capabilities = cmp.default_capabilities()
local lsp_flags = {
  -- This is the default in Nvim 0.7+
  debounce_text_changes = 50,
}

-- https://github.com/neovim/nvim-lspconfig
-- ref https://zenn.dev/botamotch/articles/21073d78bc68bf
-- Use an on_attach function to only map the following keys
-- after the language server attaches to the current buffer
local on_attach = function(client, bufnr)
  -- Enable completion triggered by <c-x><c-o>
  vim.api.nvim_buf_set_option(bufnr, "omnifunc", "v:lua.vim.lsp.omnifunc")

  -- Mappings.
  -- See `:help vim.diagnostic.*` for documentation on any of the below functions
  local bufopts = { noremap = true, silent = true, buffer = bufnr }
  vim.keymap.set("n", "<space>e", vim.diagnostic.open_float, opts)
  -- vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, opts)
  -- vim.keymap.set("n", "]d", vim.diagnostic.goto_next, opts)
  -- vim.keymap.set("n", "<space>q", vim.diagnostic.setloclist, opts)
  -- vim.keymap.set("n", "gD", vim.lsp.buf.declaration, bufopts)
  vim.keymap.set("n", "gd", vim.lsp.buf.definition, bufopts)
  -- vim.keymap.set("n", "K", vim.lsp.buf.hover, bufopts)
  vim.keymap.set("n", "gi", vim.lsp.buf.implementation, bufopts)
  -- vim.keymap.set("n", "<C-k>", vim.lsp.buf.signature_help, bufopts)
  -- vim.keymap.set("n", "<space>wa", vim.lsp.buf.add_workspace_folder, bufopts)
  -- vim.keymap.set("n", "<space>wr", vim.lsp.buf.remove_workspace_folder, bufopts)
  vim.keymap.set("n", "<space>wl", function()
    print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
  end, bufopts)
  -- vim.keymap.set("n", "<space>D", vim.lsp.buf.type_definition, bufopts)
  vim.keymap.set("n", "<space>rn", vim.lsp.buf.rename, bufopts)
  -- vim.keymap.set("n", "<space>ca", vim.lsp.buf.code_action, bufopts)
  -- vim.keymap.set("n", "gr", vim.lsp.buf.references, bufopts)
  vim.keymap.set("n", "<space>f", function() vim.lsp.buf.format { async = true } end, bufopts)
end

lspconfig["jedi_language_server"].setup {
  on_attach = on_attach,
  flags = lsp_flags,
}
lspconfig["tsserver"].setup {
  on_attach = on_attach,
  flags = lsp_flags,
}
lspconfig["rust_analyzer"].setup {
  on_attach = on_attach,
  flags = lsp_flags,
  -- Server-specific settings...
  settings = {
    ["rust-analyzer"] = {}
  }
}
lspconfig["lua_ls"].setup {
-- lspconfig["sumneko_lua"].setup {
  on_attach = on_attach,
  flags = lsp_flags,
}
lspconfig["zls"].setup {
  on_attach = on_attach,
  flags = lsp_flags,
}

--lspconfig["yamlls"].setup{
lspconfig.yamlls.setup {
  on_attach = on_attach,
  capabilities = capabilities,
  settings = {
    yaml = {
      schemas = {
        ["https://raw.githubusercontent.com/quantumblacklabs/kedro/develop/static/jsonschema/kedro-catalog-0.17.json"] = "conf/**/*catalog*",
        ["https://json.schemastore.org/github-workflow.json"] = "/.github/workflows/*"
      },
      schemaStore = {
        enable = true
      }
    }
  }
}
lspconfig.emmet_ls.setup({
  -- on_attach = on_attach,
  capabilities = vim.lsp.protocol.make_client_capabilities(),
  --capabilities.textDocument.completion.completionItem.snippetSupport = true,
  filetypes = { 'html', 'typescriptreact', 'javascriptreact', 'css', 'sass', 'scss', 'less' },
  init_options = {
    html = {
      options = {
        -- For possible options, see: https://github.com/emmetio/emmet/blob/master/src/config.ts#L79-L267
        ["bem.enabled"] = true,
      },
    },
  }
})

lspconfig.rnix.setup{}


-- return function()
--   local utils = require("utils._set_config")
--   local conf_lsp = utils.conf_lsp
--
--   vim.diagnostic.config({
--     virtual_text = false,
--   })
--   vim.o.updatetime = 250
--   vim.cmd([[autocmd CursorHold,CursorHoldI * lua vim.diagnostic.open_float(nil, {focus=false})]])
--
--   -- mapping
--   local servers = {
-- 	  --"denols",
-- 	  --"gopls",
--     --"jsonls",
-- 		--"rust_analyzer",
--     --"sumneko_lua",
-- 	  --"tflint",
-- 	  --"tsserver",
-- 	  --"yamlls",
-- 	  --"zls",
--     "jedi_python",
--   }
--
--   for _, lsp in ipairs(servers) do
--     conf_lsp(lsp)
--   end
-- end
