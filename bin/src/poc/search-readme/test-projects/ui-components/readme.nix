{
  description = "Reusable UI components library";
  goal = [
    "Provide consistent UI components"
    "Enable rapid frontend development"
    "Maintain design system compliance"
  ];
  nonGoal = [
    "Backend API development"
    "Data processing workflows"
  ];
  meta = {
    owner = [ "@frontend-team" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ "ui-lib" "component-storybook" ];
    devShells = [ "frontend-dev" ];
  };
}