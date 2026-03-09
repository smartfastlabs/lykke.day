import { useNavigate } from "@solidjs/router";
import { Component, onMount } from "solid-js";

const DEFAULT_ME_PATH = "/me/today";

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

    navigate(DEFAULT_ME_PATH, { replace: true });
  });

  return <div class="p-8 text-center text-stone-400">Redirecting…</div>;
};

export default MeIndexPage;
