{
  description = "Application layer services";
  goal = [
    "Orchestrate use cases"
    "Coordinate between domain and infrastructure"
    "Handle application-specific validation"
  ];
  nonGoal = [
    "Business logic"
    "Direct database access"
    "UI rendering"
  ];
  meta = {
    owner = [ "@app-team" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ ];
    apps = [ ];
    modules = [ ];
    overlays = [ ];
    devShells = [ ];
  };
}
