{
  description = "Replace with one-line summary (≤80 chars)";
  goal = [
    "Replace with what this component does"
    "Add multiple goals as needed"
  ];
  nonGoal = [
    "Replace with what this component doesn't do"
    "Add multiple non-goals as needed"
  ];
  meta = {
    owner = [ "@your-team-or-username" ];
    lifecycle = "experimental"; # or "stable" | "deprecated"
  };
  output = {
    packages = [ ]; # List package names if any
    apps = [ ]; # List app names if any  
    modules = [ ]; # List module names if any
    overlays = [ ]; # List overlay names if any
    devShells = [ ]; # List devShell names if any
  };
}