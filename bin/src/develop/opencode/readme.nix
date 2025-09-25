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
    patterns = {
      "server-to-client-to-server" = {
        status = "deprecated";
        location = "tests/simple_mock_server.sh";
        rationale = "サーバー非改変前提では価値薄";
        migration = "opencode-client orchestrate";
      };
      "client-orchestration" = {
        status = "prod-ready";
        location = "templates/multi-agent/";
        rationale = "クライアント完結で直列/並列・マージ実現";
      };
    };
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