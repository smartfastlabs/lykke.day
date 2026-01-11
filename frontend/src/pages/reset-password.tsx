import { Show, createSignal } from "solid-js";
import { A, useSearchParams } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [token, setToken] = createSignal(searchParams.token ?? "");
  const [password, setPassword] = createSignal("");
  const [confirmPassword, setConfirmPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [success, setSuccess] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!token().trim()) {
      setError("Reset token is missing");
      return;
    }

    if (!password()) {
      setError("Password is required");
      return;
    }

    if (password() !== confirmPassword()) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);
    try {
      await authAPI.resetPassword(token().trim(), password());
      setSuccess(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Unable to reset password";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="Choose a new password to get back into your account.">
      <Show
        when={!success()}
        fallback={
          <div class="space-y-6 text-center">
            <div class="space-y-2">
              <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                password reset
              </p>
              <p class="text-lg font-semibold text-stone-800">
                You're all set
              </p>
            </div>
            <p class="text-stone-600 text-sm leading-relaxed">
              Your password has been updated. You can now sign in with your new
              credentials.
            </p>
            <A
              href="/login"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Go to sign in
            </A>
          </div>
        }
      >
        <div class="text-center space-y-1">
          <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
            reset password
          </p>
          <p class="text-lg font-semibold text-stone-800">
            Set a new password
          </p>
        </div>

        <form onSubmit={handleSubmit} class="space-y-6">
          <Input
            id="token"
            placeholder="Reset token"
            value={token}
            onChange={(value) => {
              setToken(value);
              setError("");
            }}
            required
          />

          <Input
            id="password"
            type="password"
            placeholder="New password"
            value={password}
            onChange={setPassword}
            autocomplete="new-password"
            required
          />

          <Input
            id="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            autocomplete="new-password"
            required
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Updating password..."
            text="Reset password"
          />
        </form>
      </Show>
    </ModalPage>
  );
}

