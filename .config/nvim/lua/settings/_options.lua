vim.cmd[[
set encoding=utf-8
set fileencoding=utf-8
set termencoding=utf-8
]]

-- vim.cmd[[
-- let $LANG='en_US.UTF-8'
-- set guifont=Hack:h16
-- set fileencodings=utf-8,gbk,gb18030,big5,euc-jp,euc-kr,latin1
-- set fileformats=unix,dos,mac
-- set termguicolors
-- ]]

--let &termencoding = &encoding
--let &fileencoding = &encoding
--let &guess_encoding = "utf-8"

-- set $TERM=xterm-256color
--

vim.o.fileencoding = "cp850"
vim.o.fileformat = "dos"
vim.opt.encoding = "utf-8"
-- vim.opt.syntax = "enable"

vim.cmd 'colorscheme iceberg'
vim.opt.fileformat = "unix"
vim.opt.swapfile = false

--vim.opt.relativenumber = true --focus.nvim
vim.opt.cursorline = true
vim.opt.cursorcolumn = true
vim.opt.scrolloff=20

vim.opt.expandtab = true
vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.shiftwidth = 2
vim.opt.autoindent = true

vim.opt.showcmd = true
vim.opt.swapfile = false
vim.opt.virtualedit = "onemore"
vim.opt.splitright = true

vim.opt.clipboard = "unnamedplus"
--wsl copy/paste, https://mitchellt.com/2022/05/15/WSL-Neovim-Lua-and-the-Windows-Clipboard.html
--if not work clip.exe, https://github.com/microsoft/WSL/issues/5779
-- we have to edit /etc/profile
in_wsl = os.getenv('WSL_DISTRO_NAME') ~= nil
if in_wsl then
    vim.g.clipboard = {
        name = 'wsl clipboard',
        copy =  { ["+"] = { "clip.exe" },   ["*"] = { "clip.exe" } },
        paste = { ["+"] = { "nvim_paste" }, ["*"] = { "nvim_paste" } },
        cache_enabled = true
    }
end
--vim.g.clipboard = {
--  name = 'win32yank-wsl',
--  copy = {
--     + = 'win32yank.exe -i --crlf',
--     * = 'win32yank.exe -i --crlf',
--   },
--  paste = {
--     + = 'win32yank.exe -o --lf',
--     * = 'win32yank.exe -o --lf',
--  },
--  cache_enabled = false,
--}

--let g:clipboard = {
--          \   'name': 'win32yank-wsl',
--          \   'copy': {
--          \      '+': 'win32yank.exe -i --crlf',
--          \      '*': 'win32yank.exe -i --crlf',
--          \    },
--          \   'paste': {
--          \      '+': 'win32yank.exe -o --lf',
--          \      '*': 'win32yank.exe -o --lf',
--          \   },
--          \   'cache_enabled': 0,
--          \ }

vim.g["virtualenv#python"] = os.getenv("VIRTUAL_ENV")


-- quickfix
vim.cmd 'autocmd QuickfixCmdPost vimgrep call OpenQuickfixWindow()'

vim.g.shell = "/bin/zsh"
