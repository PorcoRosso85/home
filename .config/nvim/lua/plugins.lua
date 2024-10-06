local utils = require("utils._set_config")
local conf = utils.conf

vim.cmd [[packadd packer.nvim]]

require("packer").startup({
  function(use)
    use{"wbthomason/packer.nvim"}

    use("nvim-lua/plenary.nvim")

    -- lsp
    use({
      "neovim/nvim-lspconfig",
      config = conf("lspconfig"),
      requires = {
        "hrsh7th/cmp-nvim-lsp",
        "RRethy/vim-illuminate",
      },
    })
    use({
      "williamboman/mason.nvim",
      config = conf("mason"),
      requires = {
        "williamboman/mason-lspconfig.nvim",
      }
    })

    -- autocompletion
    use({
      "hrsh7th/nvim-cmp",
      event = "InsertEnter",
      requires = {
        { "hrsh7th/cmp-nvim-lsp", after = "nvim-lspconfig" },
        { "hrsh7th/cmp-cmdline", after = "nvim-cmp" },
        { "hrsh7th/cmp-path", after = "nvim-cmp" },
        { "hrsh7th/cmp-buffer", after = "nvim-cmp" },
        { "f3fora/cmp-spell", after = "nvim-cmp" },
        { "hrsh7th/cmp-vsnip", after = "nvim-cmp" },
        { "saadparwaiz1/cmp_luasnip", after = "nvim-cmp" },
        { "petertriho/cmp-git", after = "nvim-cmp" },
        { "onsails/lspkind.nvim"},
      },
      config = conf("cmp"),
    })

    -- Rust
    use({
      "rust-lang/rust.vim",
      ft = "rust",
      config = conf('rust'),
    })
    use({
      "simrat39/rust-tools.nvim",
      ft = "rust",
      config = function()
        require('rust-tools').setup({
          hover_with_actions = false,
        })
      end,
    })
  end,
})
