{
  description = "Dynamic HTTP client template for OpenCode (pre-auth assumed)";
  goal = [
    "Provide standard HTTP client pattern for OpenCode API interaction"
    "Enable rapid OpenCode client development with best practices"
    "Standardize session management and message handling workflows"
    "Support flexible provider/model selection via environment variables"
  ];
  nonGoal = [
    "Handle authentication or credential management"
    "Implement server-side OpenCode functionality"
    "Support non-HTTP communication protocols"
    "Provide complex multi-agent orchestration features"
  ];
  meta = {
    owner = [ "@opencode-dev" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ ];
    apps = [ ];
    modules = [ ];
    overlays = [ ];
    devShells = [ ];
    templateFiles = [ "README.md" "client.sh" ];
  };
}