{
  description = "Library for collecting and validating readme.nix files";
  goal = [
    "Provide index/report APIs"
    "Detect missing readme.nix in documentable directories"
    "Validate meta/output structure"
  ];
  nonGoal = [
    "Cross-repo aggregation"
    "Nickel-based schema (future)"
  ];
  meta = {
    owner = [ "@project-maintainers" ];
    lifecycle = "experimental";
  };
  output = {
    packages = [ ];
    apps = [ ];
    modules = [ ];
    overlays = [ ];
    devShells = [ ];
  };
}

