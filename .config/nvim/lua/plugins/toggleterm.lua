--vim.api.nvim_create_autocmd({ 'TermEnter' }, {
--  pattern = '*',
--  command = 'ToggleTerm',
--})

local utils = require("utils._set_mappings")
local prefix = "<C-j>t"
-- utils.nnoremap(utils.prefix.."tt", "<cmd>ToggleTerm<cr>") 
utils.nnoremap(prefix.."t", "<cmd>ToggleTerm<cr>")
utils.nnoremap(prefix.."rg", "<cmd>TermExec cmd='lazygit'<cr>")
utils.nnoremap(prefix.."rpy", "<cmd>TermExec cmd='python %'<cr>")
utils.nnoremap(prefix.."rpt", "<cmd>TermExec cmd='coverage run -m pytest -v %'<cr>")
utils.nnoremap(prefix.."rno", "<cmd>TermExec cmd='node %'<cr>")
utils.nnoremap(prefix.."rde", "<cmd>TermExec cmd='deno %'<cr>")
utils.nnoremap(prefix.."rts", "<cmd>TermExec cmd='npx tsc %'<cr>")
utils.nnoremap(prefix.."rzg", "<cmd>TermExec cmd='zig run %'<cr>")
utils.nnoremap(prefix.."rcw", "<cmd>TermExec cmd='crosshair watch %'<cr>")
utils.nnoremap(prefix.."rcc", "<cmd>TermExec cmd='crosshair check --report_all %'<cr>")
utils.nnoremap(prefix.."rsh", "<cmd>TermExec cmd='sh %'<cr>")
utils.nnoremap(prefix.."rlu", "<cmd>TermExec cmd='lua %'<cr>")

require("toggleterm").setup({
  direction = 'vertical',
--  size = 20 | function(term)
--    if term.direction == "horizontal" then
--      return 15
--    elseif term.direction == "vertical" then
--      return vim.o.columns * 0.4
--    end
--  end,
--  open_mapping = [[<c-\>]],
--  on_create = fun(t: Terminal), -- function to run when the terminal is first created
--  on_open = fun(t: Terminal), -- function to run when the terminal opens
--  on_close = fun(t: Terminal), -- function to run when the terminal closes
--  on_stdout = fun(t: Terminal, job: number, data: string[], name: string) -- callback for processing output on stdout
--  on_stderr = fun(t: Terminal, job: number, data: string[], name: string) -- callback for processing output on stderr
--  on_exit = fun(t: Terminal, job: number, exit_code: number, name: string) -- function to run when terminal process exits
--  hide_numbers = true, -- hide the number column in toggleterm buffers
--  shade_filetypes = {},
  autochdir = true, -- when neovim changes it current directory the terminal will change it's own when next it's opened
--  highlights = {
--    -- highlights which map to a highlight group name and a table of it's values
--    -- NOTE: this is only a subset of values, any group placed here will be set for the terminal window split
--    Normal = {
--      guibg = "<VALUE-HERE>",
--    },
--    NormalFloat = {
--      link = 'Normal'
--    },
--    FloatBorder = {
--      guifg = "<VALUE-HERE>",
--      guibg = "<VALUE-HERE>",
--    },
--  },
--  shade_terminals = true, -- NOTE: this option takes priority over highlights specified so if you specify Normal highlights you should set this to false
--  shading_factor = '<number>', -- the degree by which to darken to terminal colour, default: 1 for dark backgrounds, 3 for light
--  start_in_insert = true,
--  insert_mappings = true, -- whether or not the open mapping applies in insert mode
--  terminal_mappings = true, -- whether or not the open mapping applies in the opened terminals
--  persist_size = true,
--  persist_mode = true, -- if set to true (default) the previous terminal mode will be remembered
--  direction = 'vertical' | 'horizontal' | 'tab' | 'float',
  direction = 'float',
--  close_on_exit = true, -- close the terminal window when the process exits
  -- shell = vim.o.shell, -- change the default shell
  -- shell = "/bin/zsh",
  shell = "/root/.nix-profile/bin/zsh",
--  auto_scroll = true, -- automatically scroll to the bottom on terminal output
--  -- This field is only relevant if direction is set to 'float'
  float_opts = {
    -- The border key is *almost* the same as 'nvim_open_win'
    -- see :h nvim_open_win for details on borders however
    -- the 'curved' border is a custom border type
    -- not natively supported but implemented in this plugin.
    border = 'curved',   -- 'single' | 'double' | 'shadow' | 'curved' | ... other options supported by win open
    -- like `size`, width and height can be a number or function which is passed the current terminal
    width = 10,
    height = 75,
--    winblend = 1,
  },
--  winbar = {
--    enabled = false,
--    name_formatter = function(term) --  term: Terminal
--      return term.name
--    end
--  },
})
