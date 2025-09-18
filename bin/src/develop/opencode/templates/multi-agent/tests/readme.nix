{
  description = "Comprehensive test suite for multi-agent OpenCode template";
  goal = [
    "Ensure quality and reliability of multi-agent system components"
    "Provide regression prevention through comprehensive test coverage"
    "Enable safe refactoring with reliable test barriers"
    "Support continuous integration with automated test execution"
  ];
  nonGoal = [
    "Handle production deployment testing (focus on component testing)"
    "Provide performance benchmarking (use experimental/performance-tester.sh)"
    "Test external service integrations beyond mock scenarios"
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
      "test-error-handling.sh" "test-message.sh" "test-multi-server.sh"
      "test-orchestrator.sh" "test-session-manager.sh" "test-template-integration.sh"
    ];
  };
}