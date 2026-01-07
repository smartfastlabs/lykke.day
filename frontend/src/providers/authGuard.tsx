import { useNavigate } from "@solidjs/router";
import { Show, createEffect, createMemo, type ParentProps } from "solid-js";

import { useAuth } from "@/providers/auth";
import { SheppardProvider } from "@/providers/sheppard";

function AuthenticatedBoundary(props: ParentProps) {
  const navigate = useNavigate();
  const { user, isLoading, error } = useAuth();

  const isUnauthenticated = createMemo(() => !isLoading() && user() === null);

  createEffect(() => {
    if (isUnauthenticated()) {
      navigate("/login", { replace: true });
    }
  });

  if (error()) {
    return (
      <div class="p-8 text-center text-red-500">
        Unable to load your account right now. Please try again.
      </div>
    );
  }

  return (
    <Show
      when={!isLoading() && Boolean(user())}
      fallback={
        <div class="p-8 text-center text-gray-400">
          {isUnauthenticated() ? "Redirecting..." : "Loading..."}
        </div>
      }
    >
      <SheppardProvider>{props.children}</SheppardProvider>
    </Show>
  );
}

export function AuthGuard(props: ParentProps) {
  return <AuthenticatedBoundary>{props.children}</AuthenticatedBoundary>;
}
