{
  description = "Command-line utility for managing development environments and automating common tasks";
  
  goal = ''
    Streamline developer workflows by providing a unified interface for
    environment management, project scaffolding, and automation tasks
    across different programming languages and frameworks.
  '';
  
  nonGoal = ''
    Not a replacement for language-specific package managers or build tools.
    Does not aim to provide IDE functionality or complex debugging features.
  '';
  
  features = [
    "Environment management"
    "Project templates"
    "Task automation"
    "Multi-language support"
  ];
  
  status = "stable";
}