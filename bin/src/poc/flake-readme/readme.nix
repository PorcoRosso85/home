{
  description = "Pure Nix core that collects and validates readme.nix with Git-tracked boundary and ignore-based filtering";
  goal = [
    "Detect missing readme.nix only in Git-tracked directories containing non-readme .nix files"
    "Validate v1 schema and report errors/warnings"
    "Provide flake-parts module outputs (checks + readme-report)"
    "Keep core 100% Pure Nix with a single predictable behavior"
  ];
  nonGoal = [
    "Generic .gitignore parsing for arbitrary roots"
    "fd-based traversal or .no-readme markers"
    "Cross-flake documentation collection"
  ];
  meta = {
    version = "0.1.0";
    design = {
      rootBoundary = "self.outPath";
      documentableRule = "ignore-based filtering (excluding readme.nix)";
      defaultIgnore = [ ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache" ];
    };
    policy = {
      strict = false;
      driftMode = "none";
      failOnUnknownOutputKeys = false;
    };
    usage = {
      integrate = ''
        perSystem.readme = {
          enable = true;
          # root defaults to inputs.self.outPath
          # ignoreExtra = [ "dist" "build" ];
        };
      '';
      run = "nix flake check";
    };
    migration = {
      removed = [ "fd integration" ".no-readme marker" "search.mode option" ];
      alternatives = { exclude = "Use .gitignore or ignoreExtra"; };
    };
    owner = [ "@project-maintainers" ];
    lifecycle = "experimental";
  };
  output = {
    packages = [ "readme-report" ];
    apps = [ "readme-init" "readme-check" ];
    modules = [ "flakeModules.readme" ];
    overlays = [ ];
    devShells = [ ];
  };
}