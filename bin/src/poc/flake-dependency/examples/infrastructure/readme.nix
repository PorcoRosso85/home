{
  description = "Infrastructure layer for persistence and external system integration";
  goal = [
    "Handle data persistence operations"
    "Manage external API communications"
    "Provide message queue implementations"
    "Abstract database access patterns"
    "Handle file system operations"
  ];
  nonGoal = [
    "Contain business logic or domain rules"
    "Handle user interface concerns"
    "Process application-specific workflows"
    "Define domain entities or value objects"
  ];
}