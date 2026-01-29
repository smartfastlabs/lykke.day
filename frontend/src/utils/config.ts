/**
 * Application configuration
 *
 * Uses Vite environment variables (prefixed with VITE_)
 * Falls back to sensible defaults for development and production
 */

/**
 * Check if we're running in production
 *
 * Production: lykke.day domain
 * Development: anything else (localhost, etc.)
 */
export function isProduction(): boolean {
  return window.location.hostname === "lykke.day";
}

/**
 * Get the API base URL for WebSocket connections
 *
 * In development: connects directly to backend (localhost:8080)
 * In production: connects to api.lykke.day (WebSockets can't go through Netlify proxy)
 */
export function getWebSocketBaseUrl(): string {
  // Check for explicit config via environment variable
  const envUrl = import.meta.env.VITE_WEBSOCKET_BASE_URL;
  if (envUrl) {
    return envUrl;
  }

  // Default based on environment
  if (isProduction()) {
    // Production: connect to API subdomain (WebSockets can't use Netlify proxy)
    return "api.lykke.day";
  } else {
    // Development: connect directly to backend
    return "92.168.86.41:8080";
  }
}

/**
 * Get the protocol for WebSocket connections (ws or wss)
 */
export function getWebSocketProtocol(): string {
  return window.location.protocol === "https:" ? "wss:" : "ws:";
}
