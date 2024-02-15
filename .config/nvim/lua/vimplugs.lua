local utils = require("utils._set_config")
local conf = utils.conf
local Plug = require("utils._set_vimplug")

Plug.begin(vim.fn.stdpath("data").. "/plugged")

Plug("kevinhwang91/nvim-ufo", { config = function() conf("ufo") end }) --folding, collapsing
Plug("rcarriga/nvim-notify", { config = function() conf("notify") end })
Plug("kevinhwang91/promise-async")
-- Plug("Olical/conjure")
Plug("m00qek/baleia.nvim", { config = function() conf("baleia") end })
Plug("michaelb/sniprun", { config = function() conf("sniprun") end })
-- Plug("tpope/vim-dispatch")
-- Plug("rmagatti/auto-session", { config = function() conf("auto_session") end })
-- Plug("natecraddock/workspaces.nvim", { config = function() conf("workspaces_sessions") end })
-- Plug("natecraddock/sessions.nvim", { config = function() conf("workspaces_sessions") end })
-- Plug("folke/persistence.nvim", { config = function() conf("persistence") end })

Plug("nvim-lua/plenary.nvim")
-- Plug("nvim-lua/popup.nvim")
-- Plug("folke/which-key.nvim") -- containd by fzflua
Plug("folke/neodev.nvim")
-- Plug("mrjones2014/legendary.nvim", { config = function() conf("legendary") end }) -- contained by fzflua
--   Plug("stevearc/dressing.nvim", { config = function() conf("dressing") end })
Plug("lewis6991/gitsigns.nvim", { config = function() conf("gitsigns") end })
Plug("tpope/vim-fugitive")

--Plug("nvim-lualine/lualine.nvim", { config = function() conf("lualine") end })
Plug("kyazdani42/nvim-web-devicons", { config = function() conf("devicons") end })

Plug("beauwilliams/focus.nvim", { config = function() conf("focus") end })
Plug("akinsho/toggleterm.nvim", { config = function() conf("toggleterm") end })

Plug("ibhagwan/fzf-lua", { config = function() conf("fzflua") end })
-- Plug("nvim-telescope/telescope.nvim", { config = function() conf("telescope") end })
--   Plug("nvim-telescope/telescope-media-files.nvim", { config = function() conf("telescope") end })

--Plug("mattn/emmet-vim", { config = function() conf("emmet") end })
-- Plug("terrortylor/nvim-comment", { config = function() conf("nvim_comment") end })
Plug("numToStr/Comment.nvim", { config = function() conf("comment") end })
--Plug("jiangmiao/auto-pairs")

Plug("hrsh7th/nvim-cmp", { config = function() conf("cmp") end })
  Plug "hrsh7th/cmp-nvim-lsp"
  Plug "hrsh7th/cmp-buffer"
  Plug "hrsh7th/cmp-path"
  Plug "hrsh7th/cmp-cmdline"
  Plug("rinx/cmp-skkeleton")
  Plug("zbirenbaum/copilot-cmp", { config = function() conf("cmp") end })
  Plug("tzachar/cmp-tabnine", {
    --["do"] = "./install.sh", 
    config = function() conf("tabnine") end
  })

-- For vsnip users.
Plug "hrsh7th/cmp-vsnip"
Plug "hrsh7th/vim-vsnip"
-- For luasnip users.
Plug "L3MON4D3/LuaSnip"
Plug "saadparwaiz1/cmp_luasnip"

-- language server
-- Plug("williamboman/mason.nvim", { config = function() conf("mason") end })
--   Plug("williamboman/mason-lspconfig.nvim", { config = function() conf("mason") end })
--   Plug("jay-babu/mason-nvim-dap.nvim")
--   Plug("jay-babu/mason-null-ls.nvim")
Plug("neovim/nvim-lspconfig", { config = function() conf("lspconfig") end })
  Plug("onsails/lspkind.nvim", { config = function() conf("lspkind") end })
  Plug("glepnir/lspsaga.nvim", { config = function() conf("lspsaga") end })
Plug("mfussenegger/nvim-dap", { config = function() conf("dap") end })
  Plug("theHamsta/nvim-dap-virtual-text", { config = function() conf("dap_virtual_text") end })
  Plug("rcarriga/nvim-dap-ui", { config = function() conf("dap_ui") end })
  Plug("mfussenegger/nvim-dap-python", { config = function() conf("dap_python") end })
Plug("nvim-neotest/neotest", { config = function() conf("neotest") end })
  Plug("nvim-neotest/neotest-vim-test")
  Plug("vim-test/vim-test", { config = function() conf("vimtest") end })
  Plug("antoinemadec/FixCursorHold.nvim")
  Plug("andythigpen/nvim-coverage", { config = function() conf("coverage") end }) 
Plug("jose-elias-alvarez/null-ls.nvim", { config = function() conf("nullls") end })
Plug("zbirenbaum/copilot.lua", { config = function() conf("copilot") end })
Plug("codota/tabnine-nvim", { config = function() conf("tabnine") end })

-- Plug("simrat39/symbols-outline.nvim", { config = function() conf("symbols_outline") end })


--Plug "mechatroner/rainbow_csv"
Plug("chrisbra/csv.vim", { config = function() conf("csvvim") end })

-- Japanese
Plug("vim-denops/denops.vim")
Plug("vim-skk/skkeleton", { config = function() conf("skkeleton") end })
  Plug("delphinus/skkeleton_indicator.nvim", { config = function() conf("skkeleton") end })

-- setting
Plug("nvim-treesitter/nvim-treesitter", { config = function() conf("treesitter") end })
Plug("shaunsingh/nord.nvim", { config = function() conf("nord") end })
-- Plug("olimorris/onedarkpro.nvim")
Plug("cocopon/iceberg.vim")
-- Plug("folke/tokyonight.nvim")
-- Plug("folke/noice.nvim", { config = function() conf("noice") end })


Plug.ends()
