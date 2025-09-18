{
  description = "Interactive React transition demo replacing wireframes";
  goal = [
    "Provide interactive screen transition demonstration system"
    "Replace static wireframes with executable transition flows"
    "Enable stakeholder experience of actual navigation patterns"
    "Serve as implementation reference with visual badges for auth/SSR states"
  ];
  nonGoal = [
    "Full application backend implementation"
    "Production-ready authentication system"
    "External service dependencies"
    "Complex state management beyond demonstration needs"
  ];
  meta = {
    owner = [ "@project-maintainers" ];
    lifecycle = "experimental";
  };
  output = {
    packages = [ "react-transition-demo" ];
    apps = [ "demo" "dev" ];
    modules = [ ];
    overlays = [ ];
    devShells = [ "default" ];
  };
  usage = {
    quickStart = "nix run .#demo";
    development = [
      "nix develop"
      "nix run .#dev"
    ];
  };
  features = [
    "Interactive screen transition demonstration"
    "Visual badges for authentication and SSR states"
    "Breadcrumb navigation"
    "Self-contained deployment environment"
  ];
  techStack = [
    "React with 'use client'"
    "No external service dependencies"
    "Nix Flake dependency management"
  ];
}