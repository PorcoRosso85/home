{
  description = "OpenCode configuration files";
  goal = [ "Store OpenCode-specific settings" ];
  nonGoal = [ "User configuration" ];
  meta = { owner = [ "@opencode-dev" ]; lifecycle = "stable"; };
  output = { packages = []; apps = []; modules = []; overlays = []; devShells = []; };
}