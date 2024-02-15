require("mason").setup({
  ui = {
    icons = {
      package_installed = "✓",
      package_pending = "➜",
      package_uninstalled = "✗"
    }
  }
})

require("mason-lspconfig").setup {
    -- ensure_installed = { "sumneko_lua", "rust_analyzer" },
}

require("mason-lspconfig").setup_handlers {
  -- The first entry (without a key) will be the default handler
  -- and will be called for each installed server that doesn't have
  -- a dedicated handler.
  function (server_name) -- default handler (optional)
      require("lspconfig")[server_name].setup {}
  end,
  -- Next, you can provide a dedicated handler for specific servers.
  -- For example, a handler override for the `rust_analyzer`:
  -- ["rust_analyzer"] = function () require("rust-tools").setup {} end,
  --
  -- https://zenn.dev/botamotch/articles/21073d78bc68bf
  -- local opt = {
  --   capabilities = require('cmp_nvim_lsp').default_capabilities(
  --     vim.lsp.protocol.make_client_capabilities()
  --   )
  -- },
  -- require('lspconfig')[server_name].setup(opt)
}
