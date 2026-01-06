import { useNavigate } from "@solidjs/router";
import { Show, createEffect, type ParentProps } from "solid-js";

import { SheppardProvider, useSheppard } from "@/providers/sheppard";
import { ApiRequestError } from "@/utils/api";

function AuthenticatedBoundary(props: ParentProps) {
  const navigate = useNavigate();
  const { isLoading, error } = useSheppard();

  createEffect(() => {
    const currentError = error();
    if (
      currentError instanceof ApiRequestError &&
      currentError.status === 401
    ) {
      navigate("/login", { replace: true });
    }
  });

  if (error() && !(error() instanceof ApiRequestError)) {
    return (
      <div class="p-8 text-center text-red-500">
        Unable to load your account right now. Please try again.
      </div>
    );
  }

  return (
    <Show
      when={!isLoading()}
      fallback={<div class="p-8 text-center text-gray-400">Loading...</div>}
    >
      {props.children}
    </Show>
  );
}

export function AuthGuard(props: ParentProps) {
  return (
    <SheppardProvider>
      <AuthenticatedBoundary>{props.children}</AuthenticatedBoundary>
    </SheppardProvider>
  );
}
