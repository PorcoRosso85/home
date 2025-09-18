import Lake
open Lake DSL

package src {
  -- add package configuration options here
}

lean_lib Src {
  -- add library configuration options here
}

@[default_target]
lean_exe my_project {
  root := `Src.Main
}
