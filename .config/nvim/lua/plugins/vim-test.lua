local utils = require("utils._set_mappings")
utils.nnoremap("<leader>tt", "<cmd>lua require('fzf-lua').files()<cr>") 
