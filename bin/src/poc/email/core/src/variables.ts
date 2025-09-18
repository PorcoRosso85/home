// Environment variables

/**
 * Type-safe environment configuration for email invitation system
 */
export interface EnvironmentConfig {
  /** Base URL for invitation links */
  inviteBaseUrl: string;
  /** Environment mode */
  environment: 'development' | 'production';
  /** Port for local development server (if needed) */
  port: number;
}

/**
 * Load and validate environment variables
 * Following YAGNI principle - only essential configuration
 */
function loadEnvironmentConfig(): EnvironmentConfig {
  const port = parseInt(process.env.PORT || '3000', 10);
  return {
    inviteBaseUrl: process.env.INVITE_BASE_URL || 'https://invite.example.com',
    environment: (process.env.NODE_ENV as 'development' | 'production') || 'development',
    port: isNaN(port) ? 3000 : port,
  };
}

/**
 * Global configuration instance
 * Initialized once to ensure consistency
 */
export const config: EnvironmentConfig = loadEnvironmentConfig();

/**
 * Validate configuration on module load
 * Fail fast if essential configuration is missing or invalid
 */
function validateConfig(config: EnvironmentConfig): void {
  if (!config.inviteBaseUrl) {
    throw new Error('INVITE_BASE_URL is required');
  }
  
  try {
    new URL(config.inviteBaseUrl);
  } catch {
    throw new Error(`Invalid INVITE_BASE_URL: ${config.inviteBaseUrl}`);
  }
  
  if (config.port < 1 || config.port > 65535) {
    throw new Error(`Invalid PORT: ${config.port}`);
  }
}

// Validate on module initialization
validateConfig(config);