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
    summary = "Machine-readable validation hub for OpenCode flake. README.md provides human guidance via references to this file.";
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
    links = {
      readme = "README.md";
    };
    verify = {
      scripts = [
        "./.opencode/verify-basic.sh"
        "nix run /home/nixos/bin/src/poc/flake-readme#readme-check"
      ];
      commands = {
        "sync-default" = "opencode-client \"2+2?\" 1>ai.txt 2>meta.txt; test -s ai.txt && ! test -s meta.txt";
        "async-no-wait" = "opencode-client send --no-wait \"test message\" 1>ai_nowait.txt 2>meta_nowait.txt; test ! -s ai_nowait.txt && test -s meta_nowait.txt";
        "ssot-consistency" = "sid=$(grep -o 'ses_[A-Za-z0-9_]\\+' meta_nowait.txt | tail -1); opencode-client history --sid \"$sid\" --format json | jq -r '.[].parts[].text' | head -1";
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