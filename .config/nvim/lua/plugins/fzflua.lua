-- https://github.com/ibhagwan/fzf-lua
local utils = require("utils._set_mappings")
local prefix = "<C-j>f"
utils.nnoremap(prefix, "<cmd>lua require('fzf-lua').builtin()<cr>") 
vim.api.nvim_create_user_command('FFZ',"lua require('fzf-lua').builtin()", {}) 
utils.nnoremap(prefix.."c", "<cmd>lua require('fzf-lua').builtin( { query = 'command' } )<cr>") 
utils.nnoremap(prefix.."k", "<cmd>lua require('fzf-lua').builtin( { query = 'keymap' } )<cr>") 
-- vim.api.nvim_add_user_command(
--     'Upper',
--     function(opts)
--         print(string.upper(opts.args))
--     end,
--     { nargs = 1 }
-- )

utils.nnoremap(prefix.."ff", "<cmd>lua require('fzf-lua').files()<cr>") 
-- shortcut destinations
utils.nnoremap(prefix.."fc", "<cmd>lua require('fzf-lua').files({ cwd='~/.config/' })<cr>")
-- utils.nnoremap(prefix.."fm", "<cmd>lua require('fzf-lua').files({ cwd='/mnt/c/Users/admin.DESKTOP-1PF4AT3/AppData/Local/Packages/' })<cr>")
utils.nnoremap(prefix.."fm", "<cmd>lua require('fzf-lua').files({ cwd='/root/mount/' })<cr>")
utils.nnoremap(prefix.."fd", "<cmd>lcd ~|lua require('fzf-lua').files({ cmd = 'find . -maxdepth 3' })<cr>")

utils.nnoremap(prefix.."o", "<cmd>lua require('fzf-lua').oldfiles()<cr>") 
utils.nnoremap(prefix.."b", "<cmd>lua require('fzf-lua').buffers()<cr>") 
utils.nnoremap(prefix.."fp", "<cmd>lua require('fzf-lua').files({ cmd='find ..' })<cr>") 
utils.nnoremap(prefix.."fpp", "<cmd>lua require('fzf-lua').files({ cmd='find ../..' })<cr>") 
utils.nnoremap(prefix.."fppp", "<cmd>lua require('fzf-lua').files({ cmd='find ../../..' })<cr>") 
utils.nnoremap(prefix.."fpppp", "<cmd>lua require('fzf-lua').files({ cmd='find /' })<cr>") 
--utils.nnoremap("<leader>fd", "<cmd>:lua require('fzf-lua').files({ prompt='LS> ', cmd = 'ls', cwd='~/project' })<cr>")
--utils.nnoremap(prefix.."c", "<cmd>lcd %:p:h|lua require('fzf-lua').files()<cr>") 

utils.nnoremap(prefix.."fvp", "<cmd>topleft vsp|FzfLua files cwd=..<cr>") 
utils.nnoremap(prefix.."fvpp", "<cmd>topleft vsp|FzfLua files cwd=../..<cr>") 
utils.nnoremap(prefix.."fvppp", "<cmd>topleft vsp|FzfLua files cwd=../../..<cr>") 

-- utils.nnoremap(prefix.."gif", "<cmd>lua require('fzf-lua').git_files()<cr>")
-- utils.nnoremap(prefix.."gis", "<cmd>lua require('fzf-lua').git_status()<cr>")
-- utils.nnoremap(prefix.."gic", "<cmd>lua require('fzf-lua').git_commits()<cr>")
-- utils.nnoremap(prefix.."gib", "<cmd>lua require('fzf-lua').git_bcommits()<cr>")
-- utils.nnoremap(prefix.."gif", "<cmd>lua require('fzf-lua').git_branch()<cr>")
-- utils.nnoremap(prefix.."gif", "<cmd>lua require('fzf-lua').git_stash()<cr>")

-- find test file, it has 'test_' prefix to file name where to jump from
utils.nnoremap(prefix.."ft", "<cmd>lua require('fzf-lua').files({ cwd='.', query='test_' })<cr>")






return function()
  local ok, fzflua = pcall(require, "fzf-lua")

  if not ok then
    return
  end

  fzflua.setup {
    winopts = {
      h1 = { border = "FloatBorder", }
    },
    mapping = {
    }
  }
end
