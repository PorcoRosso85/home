return function()
  local ok, bufferline = pcall(require, "bufferline")
  if (not status) then return end

  bufferline.setup({
    options = {
      mode = 'tabs',
      separator_style = 'slant',
      always_show_bufferline = false,
    },
    buffer_selected = {
      gui = 'bold',
    }
  })
end

--local utils = require('utils._set_mappings')
--utils.nnoremap('<Tab>', '<cmd>BufferLineCycleNext<cr>', {})
--utils.nnoremap('<S-Tab>', '<cmd>BufferLineCyclePrev<cr>', {})


--local utils = require("utils._set_mappings")
--utils.nnoremap("<leader>ff", "<cmd>lua require('fzf-lua').files()<cr>") 
--
--return function()
--  local ok, fzflua = pcall(require, "fzf-lua")
--
--  if not ok then
--    return
--  end
--
--  fzflua.setup {
--    winopts = {
--      h1 = { border = "FloatBorder", }
--    },
--  }
--end
