{
  description = "HTTP-only two-server OpenCode development environment with templates";
  goal = [
    "Provide unified development environment for OpenCode AI assistant CLI"
    "Support both Basic Usage (nix run) and Development Usage (nix develop)"
    "Standardize OpenCode client implementations via templates"
    "Enable multi-agent system development with session management"
  ];
  nonGoal = [
    "Direct AI model hosting or training infrastructure"
    "Non-HTTP OpenCode communication protocols"
    "Production deployment configurations"
  ];
  meta = {
    owner = [ "@opencode-dev" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ "client-hello" ];
    apps = [ "client-hello" ];
    modules = [ ];
    overlays = [ ];
    devShells = [ "default" ];
    templates = [ "opencode-client" "multi-agent" ];
  };
}