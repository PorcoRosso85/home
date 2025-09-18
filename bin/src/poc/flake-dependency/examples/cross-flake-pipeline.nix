# examples/cross-flake-pipeline.nix
# Example of composing single functions for cross-flake documentation collection
# Note: This example assumes both flake-dependency and flake-readme are available as inputs
{ lib, flake-dependency, flake-readme }:
rec {
  # Example 1: Collect docs from path dependencies only (no network)
  collectPathDocs = { lockPath }:
    let
      # Step 1: Get dependency list
      depsIndex = flake-dependency.lib.deps.index { inherit lockPath; };
      
      # Step 2: Filter path dependencies
      pathDeps = lib.filter (d: d.locked.type == "path") depsIndex.deps;
      
      # Step 3: Collect docs from each path dependency
      calleeDocs = lib.listToAttrs (map (d: {
        name = d.name;
        value = flake-readme.lib.docs.index { 
          root = d.locked.path; 
        };
      }) pathDeps);
    in {
      inherit pathDeps calleeDocs;
      summary = "Collected docs from ${toString (lib.length pathDeps)} path dependencies";
    };

  # Example 2: Collect docs from GitHub dependencies (requires network)
  collectGithubDocs = { lockPath, evalInputs ? false }:
    let
      # Step 1: Get dependency list
      depsIndex = flake-dependency.lib.deps.index { inherit lockPath; };
      
      # Step 2: Filter GitHub dependencies
      githubDeps = lib.filter (d: d.locked.type == "github") depsIndex.deps;
      
      # Step 3: Collect docs (only if evalInputs is true)
      calleeDocs = if evalInputs then
        lib.listToAttrs (map (d: {
          name = d.name;
          value = 
            let
              ref = "github:${d.locked.owner}/${d.locked.repo}?rev=${d.locked.rev}";
              flake = builtins.getFlake ref;
            in
            flake-readme.lib.docs.index { 
              root = flake.outPath; 
            };
        }) githubDeps)
      else
        {};
    in {
      inherit githubDeps;
      calleeDocs = if evalInputs then calleeDocs else "Set evalInputs=true to fetch";
      summary = "Found ${toString (lib.length githubDeps)} GitHub dependencies";
    };

  # Example 3: Full pipeline - combine all dependency docs
  fullPipeline = { lockPath, includeGithub ? false }:
    let
      # Collect from different sources
      pathResults = collectPathDocs { inherit lockPath; };
      githubResults = if includeGithub then
        collectGithubDocs { inherit lockPath; evalInputs = true; }
      else
        { calleeDocs = {}; };
      
      # Merge all collected docs
      allCalleeDocs = pathResults.calleeDocs // githubResults.calleeDocs;
      
      # Get deps and docs separately from each POC
      deps = flake-dependency.lib.deps.index { inherit lockPath; };
      docs = flake-readme.lib.docs.index { root = ./.; };
    in {
      # Caller docs and deps from separate POCs
      inherit docs deps;
      
      # Extended with callee docs
      calleeDocs = allCalleeDocs;
      
      # Statistics
      stats = {
        pathDepsWithDocs = lib.length (lib.attrNames pathResults.calleeDocs);
        githubDepsWithDocs = if includeGithub then
          lib.length (lib.attrNames githubResults.calleeDocs)
        else 0;
        totalDepsAnalyzed = lib.length deps.deps;
      };
    };
}