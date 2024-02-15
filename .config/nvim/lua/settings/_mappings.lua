local utils = require("utils._set_mappings")

-- where neovim where file location is
utils.nnoremap("<leader>cd", "<cmd>lcd %:p:h|pwd<cr>")
utils.nnoremap("<leader>cde", "<cmd>lcd %:p:h|pwd|e .<cr>")
utils.nnoremap("<leader>cdp", "<cmd>lcd %:p:h|lcd ..|pwd<cr>")
utils.nnoremap("<leader>cdpe", "<cmd>lcd %:p:h|lcd ..|pwd|e .<cr>")

-- disable cross key
utils.nnoremap("<Up>", "<nop>")
utils.nnoremap("<Down>", "<nop>")
utils.nnoremap("<Left>", "<nop>")
utils.nnoremap("<Right>", "<nop>")
utils.vnoremap("<Up>", "<nop>")
utils.vnoremap("<Down>", "<nop>")
utils.vnoremap("<Left>", "<nop>")
utils.vnoremap("<Right>", "<nop>")

-- whichkey for default command
-- local whichkey = require("which-key")
-- whichkey.setup()
--
-- -- :h ins-completion
-- whichkey.register({
--   ["<C-l>"] = 'Whole lines',
--   ["<C-n>"] = 'keywords in the current file',
--   ["<C-k>"] = 'keywords in dictionary',
--   ["<C-t>"] = 'keywords in thesaurus',
--   ["<C-i>"] = 'keywords in the current and included files',
--   ["<C-]>"] = 'tags',
--   ["<C-f>"] = 'file names',
--   ["<C-d>"] = 'definitions or macros',
--   ["<C-v>"] = 'Vim command-line',
--   ["<C-u>"] = 'User defined completion',
--   ["<C-o>"] = 'omni completion',
--   ["<C-s>"] = 'Spelling suggestions',
--   ["<C-z>"] = 'stop completion',
-- }, {
--   mode = "i",
--   prefix = "<C-x>",
-- })
--
-- -- easy snipet
-- whichkey.register({
-- --  ["init"] = { "<cmd>vim.cmd('e ~/.config/nvim/')<cr>" }
-- },
-- { prefix = "<leader>" }
-- )
--

-- quickfix
-- utils.nnoremap("<leader>qf", "<nop>")


-- buffer
local buffer_prefix = "<C-j>b"
--utils.nnoremap("<C-j><C-j>", "<cmd>:bnext<cr>")
--utils.nnoremap("<C-j><C-k>", "<cmd>:bprev<cr>")
--utils.nnoremap("<C-j><C-d>", "<cmd>:bdelete<cr>")
utils.nnoremap(buffer_prefix.."b", "<cmd>:ls<cr>")
utils.nnoremap(buffer_prefix.."n", "<cmd>:bnext<cr>")
utils.nnoremap(buffer_prefix.."d", "<cmd>:bdelete<cr>")


-- terminal
--utils.nnoremap("<leader>t", "<cmd>vs|exe 'resize ' . (winwidth(0)*2/3)|exe 'resize ' . (winheight(0)*2/1)|te<cr>")
--map("n", "<C-t>", [[&bt ==# 'terminal' ? '<cmd>bdelete!<cr>' : '<cmd>split<bar>term<cr>']], {noremap = true, expr = true})
--utils.nnoremap("<C-t>", "[[&bt ==# 'terminal' ? '<cmd>bdelete!<cr>' : '<cmd>split<bar>term<cr>']], {noremap = true, expr = true}")
vim.api.nvim_create_autocmd({ 'TermOpen' }, {
  pattern = '*',
  command = 'startinsert',
})
utils.tnoremap("<C-W>n", "<cmd>new<cr>")
utils.tnoremap("<C-W><C-N>", "<cmd>new<cr>")
utils.tnoremap("<C-W>q", "<cmd>quit<cr>")
utils.tnoremap("<C-W><C-Q>", "<cmd>quit<cr>")
utils.tnoremap("<C-W>c", "<cmd>close<cr>")
utils.tnoremap("<C-W>o", "<cmd>only<cr>")
utils.tnoremap("<C-W><C-O>", "<cmd>only<cr>")
utils.tnoremap("<C-W><Down", "<cmd>wincmd j<cr>")
utils.tnoremap("<C-W><C-J>", "<cmd>wincmd j<cr>")
utils.tnoremap("<C-W>j", "<cmd>wincmd j<cr>")
utils.tnoremap("<C-W><Up> ", "<cmd>wincmd k<cr>")
utils.tnoremap("<C-W><C-K>", "<cmd>wincmd k<cr>")
utils.tnoremap("<C-W>k", "<cmd>wincmd k<cr>")
utils.tnoremap("<C-W><Left", "<cmd>wincmd h<cr>")
utils.tnoremap("<C-W><C-H>", "<cmd>wincmd h<cr>")
utils.tnoremap("<C-W><BS> ", "<cmd>wincmd h<cr>")
utils.tnoremap("<C-W>h", "<cmd>wincmd h<cr>")
utils.tnoremap("<C-W><Righ", "<cmd>wincmd l<cr>")
utils.tnoremap("<C-W><C-L>", "<cmd>wincmd l<cr>")
utils.tnoremap("<C-W>l", "<cmd>wincmd l<cr>")
utils.tnoremap("<C-W>w", "<cmd>wincmd w<cr>")
utils.tnoremap("<C-W><C-W>", "<cmd>wincmd w<cr>")
utils.tnoremap("<C-W>W", "<cmd>wincmd W<cr>")
utils.tnoremap("<C-W>t", "<cmd>wincmd t<cr>")
utils.tnoremap("<C-W><C-T>", "<cmd>wincmd t<cr>")
utils.tnoremap("<C-W>b", "<cmd>wincmd b<cr>")
utils.tnoremap("<C-W><C-B>", "<cmd>wincmd b<cr>")
utils.tnoremap("<C-W>p", "<cmd>wincmd p<cr>")
utils.tnoremap("<C-W><C-P>", "<cmd>wincmd p<cr>")
utils.tnoremap("<C-W>P", "<cmd>wincmd P<cr>")
utils.tnoremap("<C-W>r", "<cmd>wincmd r<cr>")
utils.tnoremap("<C-W><C-R>", "<cmd>wincmd r<cr>")
utils.tnoremap("<C-W>R", "<cmd>wincmd R<cr>")
utils.tnoremap("<C-W>x", "<cmd>wincmd x<cr>")
utils.tnoremap("<C-W><C-X>", "<cmd>wincmd x<cr>")
utils.tnoremap("<C-W>K", "<cmd>wincmd K<cr>")
utils.tnoremap("<C-W>J", "<cmd>wincmd J<cr>")
utils.tnoremap("<C-W>H", "<cmd>wincmd H<cr>")
utils.tnoremap("<C-W>L", "<cmd>wincmd L<cr>")
utils.tnoremap("<C-W>T", "<cmd>wincmd T<cr>")
utils.tnoremap("<C-W>=", "<cmd>wincmd =<cr>")
utils.tnoremap("<C-W>-", "<cmd>wincmd -<cr>")
utils.tnoremap("<C-W>+", "<cmd>wincmd +<cr>")
utils.tnoremap("<C-W>z", "<cmd>pclose<cr>")
utils.tnoremap("<C-W><C-Z>", "<cmd>pclose<cr>")



-- mkdir, if you haven't created directory
utils.nnoremap("<leader>mkdir", "<cmd>!mkdir -p %:h<cr>")

-- shortcut
utils.nnoremap("<leader>qcsv", "<cmd>setfiletype csv|!csview %<cr>")
