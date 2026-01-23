const SHOW_TODAY_COOKIE = "lykke_show_today";

/**
 * Short-lived session cookie: expires after 5 minutes (Max-Age),
 * or sooner if the browser session ends. Path=/ so it's sent with /me requests.
 */
export function setShowTodayCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${SHOW_TODAY_COOKIE}=1; Path=/; Max-Age=300; SameSite=Lax`;
}

export function getShowTodayCookie(): boolean {
  if (typeof document === "undefined") return false;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${SHOW_TODAY_COOKIE}=`);
  if (parts.length !== 2) return false;
  const val = parts.pop()?.split(";").shift();
  return val === "1";
}

export function clearShowTodayCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${SHOW_TODAY_COOKIE}=; Path=/; Max-Age=0`;
}
