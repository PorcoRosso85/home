venv = os.getenv('VIRTUAL_ENV')
command = string.format('%s/bin/python', venv)

require('dap-python').setup(command)
-- lua require('dap-python').setup('~/.virtualenvs/debugpy/bin/python')
--


-- `test_runners` is a table. The keys are the runner names like `unittest` or `pytest`.
-- The value is a function that takes three arguments:
-- The classname, a methodname and the opts
-- (The `opts` are coming passed through from either `test_method` or `test_class`)
-- The function must return a module name and the arguments passed to the module as list.
-- test_runners.your_runner = function(classname, methodname, opts)
--   local args = {classname, methodname}
--   return 'modulename', args
-- end
local test_runners = require('dap-python').test_runners
test_runners.pytest = function(classname, methodname, opts)
  local args = {}
  if classname then
    table.insert(args, classname)
    if methodname then
      table.insert(args, methodname)
    end
  end
  return 'pytest', args
end

-- vim.cmd([[
-- nnoremap <silent> <leader>dappym :lua require('dap-python').test_method()<CR>
-- nnoremap <silent> <leader>dappyc :lua require('dap-python').test_class()<CR>
-- vnoremap <silent> <leader>dappys <ESC>:lua require('dap-python').debug_selection()<CR>
-- ]])

local utils = require("utils._set_mappings")
utils.nnoremap("<leader>dappym", "<cmd>lua require('dap-python').test_method()<CR>")
utils.nnoremap("<leader>dappyc", "<cmd>lua require('dap-python').test_class()<CR>")
utils.vnoremap("<leader>dappys", "<ESC><cmd>lua require('dap-python').debug_selection()<CR>")
