import { useNavigate } from "@solidjs/router";
import { Component, onMount } from "solid-js";

const LAST_ME_PATH_KEY = "lykke:last-me-path";
const DEFAULT_ME_PATH = "/me/today";

const getLastMePath = (): string | null => {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem(LAST_ME_PATH_KEY);
    if (!value) return null;
    if (!value.startsWith("/me")) return null;
    if (value === "/me" || value === "/me/") return null;
    return value;
  } catch {
    return null;
  }
};

export const MeIndexPage: Component = () => {
  const navigate = useNavigate();

  onMount(() => {
    navigate(getLastMePath() ?? DEFAULT_ME_PATH, { replace: true });
  });

  return <div class="p-8 text-center text-stone-400">Redirecting…</div>;
};

export default MeIndexPage;
