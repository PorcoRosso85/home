# flake-readme Quick Reference

## ignore-only Policy Summary
**Rule**: Every directory needs `readme.nix` unless ignored

## Default Ignored
`.git` `.direnv` `node_modules` `result` `dist` `target` `.cache` `examples`

## Custom Ignore
```nix
perSystem.readme.ignoreExtra = ["custom-dir"];
```

## Check Missing
```bash
nix eval .#index.missingReadmes
```

## Basic readme.nix
```nix
{
  description = "What this directory does";
  goal = ["Primary objectives"];
  nonGoal = ["What it doesn't do"];
  meta = {};
  output = {};
}
```