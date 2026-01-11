import { Show, createSignal } from "solid-js";
import { A } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

export default function ForgotPassword() {
  const [email, setEmail] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [sent, setSent] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const value = email().trim();
    setError("");

    if (!value) {
      setError("Email is required");
      return;
    }

    setIsLoading(true);
    try {
      await authAPI.forgotPassword(value);
      setSent(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to start the password reset process";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="We'll send a secure link to reset your password.">
      <Show
        when={!sent()}
        fallback={
          <div class="space-y-6 text-center">
            <div class="space-y-2">
              <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                email sent
              </p>
              <p class="text-lg font-semibold text-stone-800">
                Check your inbox
              </p>
            </div>
            <p class="text-stone-600 text-sm leading-relaxed">
              If your account exists, you'll receive an email with a link to
              reset your password. The link will expire shortly for security.
            </p>
            <div class="space-y-2 text-sm text-stone-600">
              <A
                href="/login"
                class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
              >
                Return to sign in
              </A>
              <div>
                or{" "}
                <A
                  href="/register"
                  class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
                >
                  create an account
                </A>
              </div>
            </div>
          </div>
        }
      >
        <div class="text-center space-y-1">
          <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
            reset password
          </p>
          <p class="text-lg font-semibold text-stone-800">Forgot your password?</p>
        </div>

        <form onSubmit={handleSubmit} class="space-y-6">
          <Input
            id="email"
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(value) => {
              setEmail(value);
              setError("");
            }}
            autocomplete="email"
            required
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Sending link..."
            text="Send reset link"
          />

          <p class="text-sm text-center text-stone-600">
            Remember your password?{" "}
            <A
              href="/login"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Sign in
            </A>
            .
          </p>
        </form>
      </Show>
    </ModalPage>
  );
}

