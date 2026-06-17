/**
 * Required environment variable names (Vite prefixes with VITE_).
 * These variables must be set at build time for production deployments.
 */
const REQUIRED_ENV_VARS = ['VITE_API_URL'] as const

/**
 * Validates that all required environment variables are set.
 * In development, VITE_API_URL is optional (defaults to /api/v1 via Vite proxy).
 * In production, VITE_API_URL is required for API calls to succeed.
 * Throws a descriptive error listing all missing variables.
 */
export function validateEnv(): void {
  // In development, allow missing env vars with sensible defaults
  if (import.meta.env.DEV) {
    return
  }

  const missingVars: string[] = []

  for (const varName of REQUIRED_ENV_VARS) {
    if (!import.meta.env[varName]) {
      missingVars.push(varName)
    }
  }

  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`)
  }
}