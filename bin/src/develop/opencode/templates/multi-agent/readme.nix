{
  description = "Client/Client Orchestration (Pattern 2) - PROD READY for server-unchanged environments";
  decision = "クライアント側で直列/並列・専門性ルーティング・マージ・案内/監査を完結。サーバーは履歴保存のみ活用。";
  status = "PROD READY";
  rationale = [
    "サーバー非変更の制約下で本質機能がクライアント側で実現可能"
    "フォールバック禁止＋厚い案内の設計方針と整合"
    "複数AI専門性の協調による品質向上を実現"
    "構造化エラー案内でユーザー生産性を最大化"
  ];
  goal = [
    "Enable complex AI system development with multi-agent coordination"
    "Provide enterprise-grade error handling and recovery mechanisms"
    "Standardize session-based state management and JSON message protocols"
    "Support load-balanced multi-server environments with health checking"
    "Accelerate development with comprehensive testing and mocking frameworks"
    "Implement client-side orchestration without server modifications"
    "Support direct/parallel execution with merge strategies (vote/summary/weighted)"
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