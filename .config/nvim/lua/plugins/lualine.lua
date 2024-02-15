require('lualine').setup {
  options = {
    icons_enabled = true,
    theme = 'auto',
    component_separators = { left = '/', right = '/'},
    section_separators = { left = '/', right = '/'},
    disabled_filetypes = {
      statusline = {},
      winbar = {},
    },
    ignore_focus = {},
    always_divide_middle = true,
    globalstatus = true,
    refresh = {
      statusline = 2500,
      tabline = 2500,
      winbar = 2500,
    }
  },
  sections = {
    lualine_a = {'mode'},
    lualine_b = {'branch', 'diff', 'diagnostics'},
    lualine_c = {
      {
        'filename', file_status = true, path = 2, shorting_target = 30,
        symbols = {
          modified = '[+]',      -- Text to show when the file is modified.
          readonly = '[-]',      -- Text to show when the file is non-modifiable or readonly.
          unnamed = '[No Name]', -- Text to show for unnamed buffers.
          newfile = '[New]',     -- Text to show for new created file before first writting
        }
      }
    },
    lualine_x = {'encoding', 'fileformat', 'filetype'},
    lualine_y = {'progress'},
    lualine_z = {'location'}
  },
  inactive_sections = {
    lualine_a = {},
    lualine_b = {},
    lualine_c = {'filename'},
    lualine_x = {'location'},
    lualine_y = {},
    lualine_z = {}
  },
--  tabline = {
--    lualine_a = {'mode'},
--    lualine_b = {'branch', 'diff', 'diagnostics'},
--    lualine_c = {
--      {
--        'filename', file_status = true, path = 2, shorting_target = 30,
--        symbols = {
--          modified = '[+]',      -- Text to show when the file is modified.
--          readonly = '[-]',      -- Text to show when the file is non-modifiable or readonly.
--          unnamed = '[No Name]', -- Text to show for unnamed buffers.
--          newfile = '[New]',     -- Text to show for new created file before first writting
--        }
--      }
--    },
--    lualine_x = {'encoding', 'fileformat', 'filetype'},
--    lualine_y = {'progress'},
--    lualine_z = {'location'}
--  },
--  winbar = {
--    lualine_a = {},
--    lualine_b = {'branch'},
--    lualine_c = {'filename'},
--    lualine_x = {},
--    lualine_y = {},
--    lualine_z = {}
--  },
  inactive_winbar = {},
  extensions = {}
}
require("lualine").hide({
  place = {"tabline", "winbar"},
  unhide = false
})

vim.opt.laststatus = 3
