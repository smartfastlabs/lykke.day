import { useNavigate } from "@solidjs/router";
import { Component, onMount } from "solid-js";

const LAST_ME_PATH_KEY = "lykke:last-me-path";
const DEFAULT_ME_PATH = "/me/today";

const parseMePath = (
  path: string
): { pathname: string; searchParams: URLSearchParams } | null => {
  if (!path.startsWith("/")) return null;
  const hashIndex = path.indexOf("#");
  const pathWithoutHash = hashIndex >= 0 ? path.slice(0, hashIndex) : path;
  const queryIndex = pathWithoutHash.indexOf("?");
  const pathname =
    queryIndex >= 0 ? pathWithoutHash.slice(0, queryIndex) : pathWithoutHash;
  const query = queryIndex >= 0 ? pathWithoutHash.slice(queryIndex + 1) : "";
  return { pathname, searchParams: new URLSearchParams(query) };
};

const hasGoogleOauthCallbackParams = (path: string): boolean => {
  const parsedPath = parseMePath(path);
  if (!parsedPath) return false;
  return (
    parsedPath.searchParams.has("code") &&
    parsedPath.searchParams.has("state") &&
    parsedPath.searchParams.has("iss")
  );
};

const getLastMePath = (): string | null => {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem(LAST_ME_PATH_KEY);
    if (!value) return null;
    const parsedPath = parseMePath(value);
    if (!parsedPath) return null;
    if (!parsedPath.pathname.startsWith("/me")) return null;
    if (parsedPath.pathname === "/me" || parsedPath.pathname === "/me/")
      return null;
    if (hasGoogleOauthCallbackParams(value)) return null;
    return value;
  } catch {
    return null;
  }
};

export const MeIndexPage: Component = () => {
  const navigate = useNavigate();

  onMount(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthCode = params.get("code");
    const oauthState = params.get("state");
    if (oauthCode && oauthState) {
      const callbackParams = new URLSearchParams({
        code: oauthCode,
        state: oauthState,
      });
      window.location.replace(
        `/api/google/callback/login?${callbackParams.toString()}`
      );
      return;
    }

    navigate(getLastMePath() ?? DEFAULT_ME_PATH, { replace: true });
  });

  return <div class="p-8 text-center text-stone-400">Redirecting…</div>;
};

export default MeIndexPage;
