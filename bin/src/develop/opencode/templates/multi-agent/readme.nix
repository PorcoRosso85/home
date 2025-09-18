{
  description = "Multi-agent orchestration system template for OpenCode";
  goal = [
    "Enable complex AI system development with multi-agent coordination"
    "Provide enterprise-grade error handling and recovery mechanisms"
    "Standardize session-based state management and JSON message protocols"
    "Support load-balanced multi-server environments with health checking"
    "Accelerate development with comprehensive testing and mocking frameworks"
  ];
  nonGoal = [
    "Handle single-agent simple request-response patterns"
    "Support non-JSON communication protocols"
    "Provide manual infrastructure management without automation"
    "Maintain compatibility with BSD netcat (requires GNU netcat)"
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
    templateFiles = [ 
      "orchestrator.sh" "session-manager.sh" "message.sh" 
      "multi-server-manager.sh" "unified-error-handler.sh"
      "README.md"
    ];
    templateDirs = [ "tests" "experimental" "examples" ];
  };
}