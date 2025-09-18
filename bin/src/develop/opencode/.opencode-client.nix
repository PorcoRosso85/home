# OpenCode Directory-Local Configuration
# This file enables enhanced features for this specific directory

{
  # Session Management
  sessionManagement = {
    enabled = true;
    strategy = "directory-based";  # "directory-based" | "global" | "disabled"
    storage = "xdg";              # "xdg" | "local" | "custom"
  };

  # Provider/Model Configuration  
  defaults = {
    provider = "anthropic";
    model = "claude-3-5-sonnet";
    # Custom URL override (optional)
    # serverUrl = "http://127.0.0.1:4097";
  };

  # Project Metadata
  project = {
    name = "opencode-development";
    description = "OpenCode HTTP-only development environment";
    # Custom session naming
    sessionPrefix = "dev";
  };

  # Feature Flags
  features = {
    persistentSessions = true;
    autoReconnect = true;
    verboseLogging = false;
    multiAgent = false;  # Enables multi-agent template integration
  };

  # Advanced Configuration (Optional)
  advanced = {
    timeoutSeconds = 30;
    retryAttempts = 3;
    # Custom session validation
    validateSessions = true;
  };
}