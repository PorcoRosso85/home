require("cmp_tabnine.config"):setup({
  disable_auto_comment=false,
  debounce_ms = 150,
  max_lines = 1000,
	max_num_results = 8,
	sort = true,
	run_on_every_keystroke = true,
	snippet_placeholder = '..',
	ignored_file_types = { 
		-- default is not to ignore
		-- uncomment to ignore in lua:
		-- lua = true
	},
	show_prediction_strength = false
})
