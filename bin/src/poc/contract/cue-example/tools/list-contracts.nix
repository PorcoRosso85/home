let
  lib = import <nixpkgs/lib>;

  # Absolute path to contracts directory
  contractsPath = /home/nixos/bin/src/poc/contract/cue-example/contracts;

  # Recursively find all contract.cue files
  findContracts = dir:
    let
      contents = builtins.readDir dir;
      entries = lib.mapAttrsToList (name: type:
        let
          path = "${toString dir}/${name}";
        in
        if type == "directory" then
          # Skip hidden directories
          if lib.hasPrefix "." name then
            []
          else
            findContracts (dir + "/${name}")
        else if name == "contract.cue" && type == "regular" then
          # Found a contract file
          [ path ]
        else
          []
      ) contents;
    in
      lib.flatten entries;

  # Find all contracts
  allContracts = if builtins.pathExists contractsPath
                 then findContracts contractsPath
                 else [];

  # Sort for stable ordering (UTF-8 lexicographic)
  sortedContracts = lib.sort (a: b: a < b) allContracts;

in
  sortedContracts