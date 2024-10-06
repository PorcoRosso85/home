if vim.fn.exepath('gopls') ~= '' then
  require 'lspconfig'.gopls.setup{
    -- cutomize
  }
else
  print('go install golang.org/x/tools/gopls@latest')
end
