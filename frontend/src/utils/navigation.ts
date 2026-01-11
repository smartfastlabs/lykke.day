/**
 * Detects if the page was loaded via back/forward browser navigation
 * @returns true if navigation was via back/forward buttons, false otherwise
 */
export function isBackForwardNavigation(): boolean {
  // Check if Performance API is available
  if (typeof window === "undefined" || !window.performance) {
    return false;
  }

  // Use the Navigation Timing API Level 2
  const navigationEntries = performance.getEntriesByType(
    "navigation"
  ) as PerformanceNavigationTiming[];

  if (navigationEntries.length > 0) {
    const navEntry = navigationEntries[0];
    return navEntry.type === "back_forward";
  }

  // Fallback to deprecated API for older browsers
  if (performance.navigation) {
    return performance.navigation.type === performance.navigation.TYPE_BACK_FORWARD;
  }

  return false;
}
