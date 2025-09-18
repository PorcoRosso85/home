{
  description = "Example project using flake-parts with readme validation";
  goal = [
    "Demonstrate flake-parts integration"
    "Show minimal configuration example"
  ];
  nonGoal = [
    "Complex multi-package setup"
    "Production deployment configuration"
  ];
  meta = {
    owner = [ "@example-team" ];
    lifecycle = "experimental";
  };
  output = {
    packages = [ "hello" ];
    apps = [ ];
    modules = [ ];
    overlays = [ ];
    devShells = [ ];
  };
}