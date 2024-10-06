vim.fn.sign_define('DapBreakpoint',{ text ='🟥', texthl ='', linehl ='', numhl =''})
vim.fn.sign_define('DapStopped',{ text ='▶️', texthl ='', linehl ='', numhl =''})

local utils = require("utils._set_mappings")
utils.nnoremap("<C-j>db", "<cmd>lua require'dap'.toggle_breakpoint()<cr>")
utils.nnoremap("<C-j>dj", "<cmd>lua require'dap'.continue()<cr>")
utils.nnoremap("<C-j>ds", "<cmd>lua require'dap'.step_over()<cr>")
utils.nnoremap("<C-j>dS", "<cmd>lua require'dap'.step_into()<cr>")
utils.nnoremap("<C-j>dr", "<cmd>lua require'dap'.repl.open()<cr>")

-- https://alpha2phi.medium.com/neovim-for-beginners-debugging-using-dap-44626a767f57

-- python
-- function M.setup(_)
--   require("dap-python").setup("python", {})
-- end
-- local venv
-- local dap = require('dap')
-- dap.adapters.python = {
--   type = 'executable';
--   -- command = 'path/to/virtualenvs/debugpy/bin/python';
--   -- command = os.getenv("VIRTUAL_ENV") .. "/bin/python";
--   args = { '-m', 'debugpy.adapter' };
-- }
--
-- dap.configurations.python = {
--   {
--     -- The first three options are required by nvim-dap
--     type = 'python'; -- the type here established the link to the adapter definition: `dap.adapters.python`
--     request = 'launch';
--     name = "Launch file";
--
--     -- Options below are for debugpy, see https://github.com/microsoft/debugpy/wiki/Debug-configuration-settings for supported options
--
--     program = "${file}"; -- This configuration will launch the current file if used.
--     pythonPath = function()
--       -- debugpy supports launching an application with a different interpreter then the one used to launch debugpy itself.
--       -- The code below looks for a `venv` or `.venv` folder in the current directly and uses the python within.
--       -- You could adapt this - to for example use the `VIRTUAL_ENV` environment variable.
--       local cwd = vim.fn.getcwd()
--       if vim.fn.executable(cwd .. '/venv/bin/python') == 1 then
--         return cwd .. '/venv/bin/python'
--       elseif vim.fn.executable(cwd .. '/.venv/bin/python') == 1 then
--         return cwd .. '/.venv/bin/python'
--       else
--         return '/usr/bin/python'
--       end
--     end;
--   },
-- }


-- lua
local M = {}
function M.setup()
  local dap = require "dap"
  dap.configurations.lua = {
    {
      type = "nlua",
      request = "attach",
      name = "Attach to running Neovim instance",
      host = function()
        local value = vim.fn.input "Host [127.0.0.1]: "
        if value ~= "" then
          return value
        end
        return "127.0.0.1"
      end,
      port = function()
        local val = tonumber(vim.fn.input("Port: ", "54321"))
        assert(val, "Please provide a port number")
        return val
      end,
    },
  }

  dap.adapters.nlua = function(callback, config)
    callback { type = "server", host = config.host, port = config.port }
  end
end

return M
