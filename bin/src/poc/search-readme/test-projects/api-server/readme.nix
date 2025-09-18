{
  description = "REST API server for user management";
  goal = [
    "Provide REST endpoints for user operations"
    "Handle authentication and authorization"
    "Manage user sessions securely"
  ];
  nonGoal = [
    "Data processing or analytics"
    "Frontend UI development"
  ];
  meta = {
    owner = [ "@backend-team" ];
    lifecycle = "experimental";
  };
  output = {
    packages = [ "api-server" ];
    apps = [ "start-server" ];
    devShells = [ "api-dev" ];
  };
}