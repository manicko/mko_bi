/**
 * Token refresh handler registration module.
 *
 * This module provides a callback registration pattern to break the circular
 * dependency between shared/api/axiosInstance.ts and features/auth/api/authApi.ts.
 * The shared layer never imports from feature modules; features register their
 * handlers at initialization time.
 */

import type { Token } from "../types/api.types"

type RefreshHandler = () => Promise<Token>

let refreshHandler: RefreshHandler | null = null

/**
 * Register the token refresh handler from the auth feature module.
 * Should be called during app initialization.
 */
export function registerRefreshHandler(handler: RefreshHandler): void {
  refreshHandler = handler
}

/**
 * Get the registered refresh handler.
 */
export function getRefreshHandler(): RefreshHandler | null {
  return refreshHandler
}