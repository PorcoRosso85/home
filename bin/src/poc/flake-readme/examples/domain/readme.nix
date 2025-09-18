{
  description = "Business logic core";
  goal = [
    "Define entities and value objects"
    "Implement domain services"
    "Enforce business rules"
  ];
  nonGoal = [
    "Persistence implementation"
    "External API calls"
    "UI concerns"
  ];
  meta = {
    owner = [ "@domain-team" ];
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
