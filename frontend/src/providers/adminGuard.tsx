import { useNavigate } from "@solidjs/router";
import { Show, createEffect, createMemo, type ParentProps } from "solid-js";

import { useAuth } from "@/providers/auth";

export function AdminGuard(props: ParentProps) {
  const navigate = useNavigate();
  const { user, isLoading } = useAuth();

  const isNotSuperuser = createMemo(
    () => !isLoading() && (!user() || !user()?.is_superuser),
  );

  createEffect(() => {
    if (isNotSuperuser()) {
      navigate("/me/today", { replace: true });
    }
  });

  return (
    <Show
      when={!isLoading() && user()?.is_superuser}
      fallback={
        <div class="p-8 text-center text-gray-400">
          {isNotSuperuser() ? "Redirecting..." : "Loading..."}
        </div>
      }
    >
      {props.children}
    </Show>
  );
}
